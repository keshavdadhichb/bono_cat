"""
Base generator interface for all demographic categories.

This module defines the abstract interface that all category-specific
generators must implement, enabling easy addition of new demographics
(Infants, Girls, etc.) in the future.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from pathlib import Path


@dataclass
class GenerationConfig:
    """Configuration for AI model generation."""
    
    category: str
    age_range: tuple
    brand: str
    style_keywords: List[str] = field(default_factory=list)
    resolution: int = 4096
    
    # Model generation settings
    num_inference_steps: int = 30
    guidance_scale: float = 7.5
    
    # Virtual try-on settings
    preserve_logo: bool = True
    garment_mask_dilate: int = 5


@dataclass
class GenerationResult:
    """Result of a generation job."""
    
    success: bool
    output_path: Optional[str] = None
    job_id: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Additional output paths
    full_body_path: Optional[str] = None
    closeup_path: Optional[str] = None


class BaseGenerator(ABC):
    """
    Abstract base class for all category-specific generators.
    
    Each demographic (teen boys, infants, girls, etc.) should have its own
    implementation that inherits from this class.
    
    Example:
        class TeenBoyGenerator(BaseGenerator):
            def get_model_prompt(self) -> str:
                return "photorealistic teen boy model..."
    """
    
    def __init__(self, runpod_client: Any, config: Optional[GenerationConfig] = None):
        """
        Initialize the generator.
        
        Args:
            runpod_client: Client for RunPod API communication
            config: Optional generation configuration
        """
        self.runpod_client = runpod_client
        self.config = config or self._get_default_config()
    
    @abstractmethod
    def _get_default_config(self) -> GenerationConfig:
        """Return the default configuration for this generator."""
        pass
    
    @abstractmethod
    def get_model_prompt(self) -> str:
        """
        Return the prompt for generating the base AI model.
        
        This prompt should describe the model characteristics like age,
        ethnicity, pose, and style appropriate for the demographic.
        
        Returns:
            str: The positive prompt for model generation
        """
        pass
    
    @abstractmethod
    def get_negative_prompt(self) -> str:
        """
        Return the negative prompt to avoid unwanted artifacts.
        
        Returns:
            str: The negative prompt for model generation
        """
        pass
    
    @abstractmethod
    def get_vto_config(self) -> Dict[str, Any]:
        """
        Return virtual try-on specific configuration.
        
        Different demographics may require different VTO settings
        (e.g., infants use inpainting instead of IDM-VTON).
        
        Returns:
            dict: Configuration for the virtual try-on node
        """
        pass
    
    def get_workflow_overrides(self) -> Dict[str, Any]:
        """
        Return any workflow-specific overrides.
        
        Override this method to customize ComfyUI workflow nodes
        for specific demographics.
        
        Returns:
            dict: Node overrides for the ComfyUI workflow
        """
        return {}
    
    async def generate_model(self) -> GenerationResult:
        """
        Generate a base AI model image.
        
        Returns:
            GenerationResult: The result of the generation
        """
        workflow = self._build_model_generation_workflow()
        result = await self.runpod_client.submit_job(workflow)
        return GenerationResult(
            success=result.get("success", False),
            output_path=result.get("output_path"),
            job_id=result.get("job_id"),
            error=result.get("error")
        )
    
    async def apply_virtual_tryon(
        self,
        model_image_path: str,
        garment_image_path: str
    ) -> GenerationResult:
        """
        Apply the garment to the generated model using virtual try-on.
        
        Args:
            model_image_path: Path to the AI model image
            garment_image_path: Path to the flat-lay garment image
            
        Returns:
            GenerationResult: The result with the try-on applied
        """
        workflow = self._build_vto_workflow(model_image_path, garment_image_path)
        result = await self.runpod_client.submit_job(workflow)
        return GenerationResult(
            success=result.get("success", False),
            output_path=result.get("output_path"),
            job_id=result.get("job_id"),
            error=result.get("error")
        )
    
    async def process(self, garment_image_path: str) -> GenerationResult:
        """
        Complete processing pipeline for a single garment.
        
        This is the main entry point that orchestrates:
        1. Model generation
        2. Virtual try-on application
        3. Face detailing and upscaling
        
        Args:
            garment_image_path: Path to the flat-lay garment image
            
        Returns:
            GenerationResult: The final processed result
        """
        # Build complete workflow
        workflow = self._build_complete_workflow(garment_image_path)
        
        # Submit to RunPod
        result = await self.runpod_client.submit_job(workflow)
        
        if not result.get("success"):
            return GenerationResult(
                success=False,
                error=result.get("error", "Unknown error during processing")
            )
        
        return GenerationResult(
            success=True,
            output_path=result.get("output_path"),
            full_body_path=result.get("full_body_path"),
            closeup_path=result.get("closeup_path"),
            job_id=result.get("job_id"),
            metadata={
                "garment": garment_image_path,
                "category": self.config.category,
                "brand": self.config.brand
            }
        )
    
    def _build_model_generation_workflow(self) -> Dict[str, Any]:
        """Build the ComfyUI workflow for model generation."""
        return {
            "prompt": self.get_model_prompt(),
            "negative_prompt": self.get_negative_prompt(),
            "steps": self.config.num_inference_steps,
            "cfg_scale": self.config.guidance_scale,
            "resolution": self.config.resolution
        }
    
    def _build_vto_workflow(
        self,
        model_image_path: str,
        garment_image_path: str
    ) -> Dict[str, Any]:
        """Build the ComfyUI workflow for virtual try-on."""
        return {
            "model_image": model_image_path,
            "garment_image": garment_image_path,
            "vto_config": self.get_vto_config()
        }
    
    def _build_complete_workflow(self, garment_image_path: str) -> Dict[str, Any]:
        """Build the complete ComfyUI workflow with all stages."""
        return {
            "type": "complete_pipeline",
            "model_prompt": self.get_model_prompt(),
            "negative_prompt": self.get_negative_prompt(),
            "garment_image": garment_image_path,
            "vto_config": self.get_vto_config(),
            "config": {
                "steps": self.config.num_inference_steps,
                "cfg_scale": self.config.guidance_scale,
                "resolution": self.config.resolution,
                "preserve_logo": self.config.preserve_logo
            },
            "overrides": self.get_workflow_overrides()
        }
