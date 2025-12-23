"""
Image processing utilities.
"""

from pathlib import Path
from typing import Tuple, Optional, List
import os

from PIL import Image, ImageOps, ImageEnhance
import structlog

logger = structlog.get_logger()


class ImageProcessor:
    """
    Utility class for image processing operations.
    
    Provides helpers for resizing, cropping, and preparing
    images for the pipeline.
    """
    
    SUPPORTED_FORMATS = {'.png', '.jpg', '.jpeg', '.webp'}
    
    @staticmethod
    def is_valid_image(path: str) -> bool:
        """Check if a file is a valid image."""
        if not os.path.exists(path):
            return False
        ext = Path(path).suffix.lower()
        return ext in ImageProcessor.SUPPORTED_FORMATS
    
    @staticmethod
    def get_image_info(path: str) -> dict:
        """Get image dimensions and format."""
        try:
            with Image.open(path) as img:
                return {
                    "width": img.width,
                    "height": img.height,
                    "format": img.format,
                    "mode": img.mode,
                    "size_bytes": os.path.getsize(path)
                }
        except Exception as e:
            logger.error("Failed to get image info", path=path, error=str(e))
            return {}
    
    @staticmethod
    def resize_image(
        input_path: str,
        output_path: str,
        size: Tuple[int, int],
        maintain_aspect: bool = True
    ) -> str:
        """
        Resize an image.
        
        Args:
            input_path: Source image path
            output_path: Destination path
            size: Target (width, height)
            maintain_aspect: Whether to maintain aspect ratio
            
        Returns:
            str: Path to resized image
        """
        with Image.open(input_path) as img:
            if maintain_aspect:
                img.thumbnail(size, Image.Resampling.LANCZOS)
            else:
                img = img.resize(size, Image.Resampling.LANCZOS)
            
            # Ensure output directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            img.save(output_path, quality=95)
        
        return output_path
    
    @staticmethod
    def create_closeup(
        input_path: str,
        output_path: str,
        focus_region: str = "upper"
    ) -> str:
        """
        Create a closeup/detail crop from an image.
        
        Args:
            input_path: Source image path
            output_path: Destination path
            focus_region: "upper" for chest/logo area, "center" for middle
            
        Returns:
            str: Path to cropped image
        """
        with Image.open(input_path) as img:
            w, h = img.size
            
            if focus_region == "upper":
                # Focus on upper 40% (chest/logo area)
                crop_box = (
                    int(w * 0.15),  # Left
                    int(h * 0.1),   # Top
                    int(w * 0.85),  # Right
                    int(h * 0.5)    # Bottom
                )
            elif focus_region == "center":
                # Center crop
                crop_box = (
                    int(w * 0.2),
                    int(h * 0.25),
                    int(w * 0.8),
                    int(h * 0.75)
                )
            else:
                # Default to upper
                crop_box = (0, 0, w, int(h * 0.5))
            
            cropped = img.crop(crop_box)
            
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            cropped.save(output_path, quality=95)
        
        return output_path
    
    @staticmethod
    def enhance_image(
        input_path: str,
        output_path: str,
        contrast: float = 1.05,
        brightness: float = 1.02,
        sharpness: float = 1.1,
        saturation: float = 1.0
    ) -> str:
        """
        Apply basic enhancements to an image.
        
        Args:
            input_path: Source image path
            output_path: Destination path
            contrast: Contrast factor (1.0 = no change)
            brightness: Brightness factor
            sharpness: Sharpness factor
            saturation: Color saturation factor
            
        Returns:
            str: Path to enhanced image
        """
        with Image.open(input_path) as img:
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Apply enhancements
            if contrast != 1.0:
                img = ImageEnhance.Contrast(img).enhance(contrast)
            if brightness != 1.0:
                img = ImageEnhance.Brightness(img).enhance(brightness)
            if sharpness != 1.0:
                img = ImageEnhance.Sharpness(img).enhance(sharpness)
            if saturation != 1.0:
                img = ImageEnhance.Color(img).enhance(saturation)
            
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            img.save(output_path, quality=95)
        
        return output_path
    
    @staticmethod
    def prepare_garment_image(
        input_path: str,
        output_path: str,
        target_size: int = 1024
    ) -> str:
        """
        Prepare a garment image for virtual try-on.
        
        - Ensures RGB mode
        - Resizes to standard size
        - Adds padding if needed
        
        Args:
            input_path: Source garment image
            output_path: Prepared image path
            target_size: Target dimension
            
        Returns:
            str: Path to prepared image
        """
        with Image.open(input_path) as img:
            # Convert to RGB
            if img.mode == 'RGBA':
                # Create white background
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize maintaining aspect ratio
            img.thumbnail((target_size, target_size), Image.Resampling.LANCZOS)
            
            # Pad to square if needed
            if img.size[0] != img.size[1]:
                new_img = Image.new('RGB', (target_size, target_size), (255, 255, 255))
                offset = (
                    (target_size - img.size[0]) // 2,
                    (target_size - img.size[1]) // 2
                )
                new_img.paste(img, offset)
                img = new_img
            
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            img.save(output_path, quality=95)
        
        return output_path
    
    @staticmethod
    def batch_process(
        input_paths: List[str],
        output_dir: str,
        operation: str = "prepare"
    ) -> List[str]:
        """
        Process multiple images.
        
        Args:
            input_paths: List of input image paths
            output_dir: Output directory
            operation: "prepare", "enhance", or "resize"
            
        Returns:
            list: Paths to processed images
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        results = []
        for path in input_paths:
            filename = Path(path).name
            output_path = str(Path(output_dir) / filename)
            
            try:
                if operation == "prepare":
                    ImageProcessor.prepare_garment_image(path, output_path)
                elif operation == "enhance":
                    ImageProcessor.enhance_image(path, output_path)
                else:
                    ImageProcessor.resize_image(path, output_path, (1024, 1024))
                
                results.append(output_path)
                logger.debug("Processed image", input=path, output=output_path)
                
            except Exception as e:
                logger.error("Failed to process image", path=path, error=str(e))
        
        return results
