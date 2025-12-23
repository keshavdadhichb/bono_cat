"""
Teen Boy Generator (Phase 1) - Ages 13-15

This module implements the generator for the Bono brand targeting
teen boys with a cool, streetwear aesthetic.
"""

from typing import Dict, Any, Optional
from .base import BaseGenerator, GenerationConfig, GenerationResult


class TeenBoyGenerator(BaseGenerator):
    """
    Generator for Teen Boys category (13-15 years).
    
    Brand: Bono
    Style: Energetic, Cool, "Gen Z" aesthetic
    Target: Indian/International teen models
    """
    
    # Curated prompts for high-quality teen model generation
    POSITIVE_PROMPT = """
    photorealistic fashion photography of a teenage boy, age 14-15 years old,
    fair skin north Indian ethnicity, handsome youthful face, bright eyes,
    confident natural expression with subtle smile,
    athletic slim build, standing in a cool relaxed pose,
    professional studio lighting, soft diffused key light,
    clean neutral grey studio background,
    fashion catalog style, editorial quality,
    wearing a stylish casual t-shirt,
    sharp focus on face and clothing details,
    high fashion magazine aesthetic,
    8k resolution, hyperrealistic, professional photography
    """.strip().replace('\n', ' ')
    
    NEGATIVE_PROMPT = """
    deformed, distorted, disfigured, poorly drawn, bad anatomy,
    wrong anatomy, extra limbs, missing limbs, floating limbs,
    disconnected limbs, mutation, mutated, ugly, disgusting,
    blurry, low quality, low resolution, pixelated,
    watermark, text, logo, signature, jpeg artifacts,
    poorly drawn hands, poorly drawn feet, poorly drawn face,
    out of frame, extra fingers, mutated hands, 
    poorly drawn hands, poorly drawn feet,
    deformed body, deformed face, deformed fingers,
    bad proportions, gross proportions, 
    cartoon, anime, 3d render, illustration, painting
    """.strip().replace('\n', ' ')
    
    # Diverse pose variations for variety in catalog
    POSE_VARIATIONS = [
        "standing straight with hands in pockets, relaxed confident pose",
        "slight side angle, one hand adjusting collar, casual cool vibe",
        "arms crossed, looking at camera with friendly smile",
        "hands at sides, walking pose, dynamic movement",
        "leaning slightly, hands behind back, editorial pose"
    ]
    
    def __init__(self, runpod_client: Any, config: Optional[GenerationConfig] = None):
        """Initialize the Teen Boy generator."""
        super().__init__(runpod_client, config)
        self._pose_index = 0
    
    def _get_default_config(self) -> GenerationConfig:
        """Return default configuration for teen boys."""
        return GenerationConfig(
            category="teen_boy",
            age_range=(13, 15),
            brand="bono",
            style_keywords=[
                "streetwear",
                "casual",
                "cool",
                "gen-z",
                "energetic"
            ],
            resolution=4096,
            num_inference_steps=35,
            guidance_scale=7.0,
            preserve_logo=True,
            garment_mask_dilate=5
        )
    
    def get_model_prompt(self) -> str:
        """Return the prompt for generating a teen boy model."""
        return self.POSITIVE_PROMPT
    
    def get_model_prompt_with_pose(self, pose_index: Optional[int] = None) -> str:
        """
        Return prompt with a specific pose variation.
        
        Args:
            pose_index: Optional index for pose variation
            
        Returns:
            str: Complete prompt with pose description
        """
        if pose_index is None:
            pose_index = self._pose_index
            self._pose_index = (self._pose_index + 1) % len(self.POSE_VARIATIONS)
        
        pose = self.POSE_VARIATIONS[pose_index % len(self.POSE_VARIATIONS)]
        return f"{self.POSITIVE_PROMPT}, {pose}"
    
    def get_negative_prompt(self) -> str:
        """Return the negative prompt for teen boy generation."""
        return self.NEGATIVE_PROMPT
    
    def get_vto_config(self) -> Dict[str, Any]:
        """
        Return virtual try-on configuration for teen boys.
        
        Uses IDM-VTON with settings optimized for preserving
        brand logos and text on t-shirts.
        """
        return {
            "method": "idm_vton",
            "model_type": "teen_male",
            "settings": {
                # Preserve logo/text visibility
                "preserve_text": True,
                "text_preservation_strength": 0.85,
                
                # Garment fitting
                "garment_mask_dilate": self.config.garment_mask_dilate,
                "garment_mask_blur": 3,
                
                # Quality settings
                "denoise_strength": 0.75,
                "guidance_scale": 7.0,
                "num_inference_steps": 30,
                
                # Body fitting
                "body_type": "athletic_slim",
                "fit_style": "regular"
            }
        }
    
    def get_workflow_overrides(self) -> Dict[str, Any]:
        """Return workflow-specific overrides for teen boys."""
        return {
            # FaceDetailer settings for sharp, youthful features
            "face_detailer": {
                "detail_method": "enhanced",
                "sharpness": 0.8,
                "eye_enhancement": True,
                "skin_smoothing": 0.3,  # Light smoothing for natural look
            },
            
            # Upscaler settings
            "upscaler": {
                "method": "ultimate_sd_upscale",
                "scale_factor": 4,  # Output at 4K
                "tile_size": 512,
                "tile_overlap": 64,
                "denoise_strength": 0.2
            },
            
            # Lighting adjustments
            "post_processing": {
                "contrast": 1.05,
                "brightness": 1.02,
                "saturation": 1.0,
                "sharpening": 0.1
            }
        }
    
    async def process_batch(
        self,
        garment_paths: list,
        use_varied_poses: bool = True
    ) -> list[GenerationResult]:
        """
        Process multiple garments with pose variation.
        
        Args:
            garment_paths: List of paths to garment images
            use_varied_poses: Whether to vary poses across the batch
            
        Returns:
            list: List of GenerationResult objects
        """
        results = []
        
        for i, garment_path in enumerate(garment_paths):
            # Use varied poses for a more dynamic catalog
            if use_varied_poses:
                pose_index = i % len(self.POSE_VARIATIONS)
                prompt = self.get_model_prompt_with_pose(pose_index)
            else:
                prompt = self.get_model_prompt()
            
            # Build workflow with the specific pose
            workflow = self._build_complete_workflow(garment_path)
            workflow["model_prompt"] = prompt
            
            # Submit job
            result = await self.runpod_client.submit_job(workflow)
            
            results.append(GenerationResult(
                success=result.get("success", False),
                output_path=result.get("output_path"),
                full_body_path=result.get("full_body_path"),
                closeup_path=result.get("closeup_path"),
                job_id=result.get("job_id"),
                error=result.get("error"),
                metadata={
                    "garment": garment_path,
                    "pose_index": i % len(self.POSE_VARIATIONS) if use_varied_poses else 0,
                    "category": self.config.category,
                    "brand": self.config.brand
                }
            ))
        
        return results
