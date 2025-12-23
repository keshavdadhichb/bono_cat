"""
Configuration management for the pipeline.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from dotenv import load_dotenv
import json


@dataclass
class RunPodConfig:
    """RunPod API configuration."""
    api_key: str
    endpoint_id: str
    timeout: int = 300  # 5 minutes default timeout
    poll_interval: int = 5  # seconds between status checks


@dataclass
class GoogleDriveConfig:
    """Google Drive configuration."""
    credentials_path: str
    input_folder_id: str
    output_folder_id: str
    scopes: list = field(default_factory=lambda: [
        'https://www.googleapis.com/auth/drive.file',
        'https://www.googleapis.com/auth/drive.readonly'
    ])


@dataclass
class PipelineConfig:
    """Main pipeline configuration."""
    category: str = "teen_boy"
    brand: str = "bono"
    output_resolution: int = 4096
    batch_size: int = 5
    log_level: str = "INFO"
    
    # Paths
    assets_dir: Path = field(default_factory=lambda: Path("assets"))
    output_dir: Path = field(default_factory=lambda: Path("output"))
    temp_dir: Path = field(default_factory=lambda: Path("temp"))


class Config:
    """Central configuration manager."""
    
    def __init__(
        self,
        runpod: RunPodConfig,
        google_drive: GoogleDriveConfig,
        pipeline: PipelineConfig
    ):
        self.runpod = runpod
        self.google_drive = google_drive
        self.pipeline = pipeline
    
    @classmethod
    def from_env(cls, env_path: Optional[str] = None) -> "Config":
        """Load configuration from environment variables."""
        if env_path:
            load_dotenv(env_path)
        else:
            load_dotenv()
        
        runpod = RunPodConfig(
            api_key=os.getenv("RUNPOD_API_KEY", ""),
            endpoint_id=os.getenv("RUNPOD_ENDPOINT_ID", ""),
            timeout=int(os.getenv("RUNPOD_TIMEOUT", "300")),
            poll_interval=int(os.getenv("RUNPOD_POLL_INTERVAL", "5"))
        )
        
        google_drive = GoogleDriveConfig(
            credentials_path=os.getenv("GOOGLE_DRIVE_CREDENTIALS_PATH", "./credentials.json"),
            input_folder_id=os.getenv("GOOGLE_DRIVE_INPUT_FOLDER_ID", ""),
            output_folder_id=os.getenv("GOOGLE_DRIVE_OUTPUT_FOLDER_ID", "")
        )
        
        pipeline = PipelineConfig(
            category=os.getenv("DEFAULT_CATEGORY", "teen_boy"),
            brand=os.getenv("DEFAULT_BRAND", "bono"),
            output_resolution=int(os.getenv("OUTPUT_RESOLUTION", "4096")),
            batch_size=int(os.getenv("BATCH_SIZE", "5")),
            log_level=os.getenv("LOG_LEVEL", "INFO")
        )
        
        return cls(runpod, google_drive, pipeline)
    
    @classmethod
    def from_json(cls, json_path: str) -> "Config":
        """Load configuration from a JSON file."""
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        runpod = RunPodConfig(**data.get("runpod", {}))
        google_drive = GoogleDriveConfig(**data.get("google_drive", {}))
        pipeline = PipelineConfig(**data.get("pipeline", {}))
        
        return cls(runpod, google_drive, pipeline)
    
    def validate(self) -> bool:
        """Validate that required configuration is present."""
        errors = []
        
        if not self.runpod.api_key:
            errors.append("RUNPOD_API_KEY is required")
        if not self.runpod.endpoint_id:
            errors.append("RUNPOD_ENDPOINT_ID is required")
        if not self.google_drive.input_folder_id:
            errors.append("GOOGLE_DRIVE_INPUT_FOLDER_ID is required")
        if not self.google_drive.output_folder_id:
            errors.append("GOOGLE_DRIVE_OUTPUT_FOLDER_ID is required")
        
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "runpod": {
                "endpoint_id": self.runpod.endpoint_id,
                "timeout": self.runpod.timeout,
                "poll_interval": self.runpod.poll_interval
            },
            "google_drive": {
                "credentials_path": self.google_drive.credentials_path,
                "input_folder_id": self.google_drive.input_folder_id,
                "output_folder_id": self.google_drive.output_folder_id
            },
            "pipeline": {
                "category": self.pipeline.category,
                "brand": self.pipeline.brand,
                "output_resolution": self.pipeline.output_resolution,
                "batch_size": self.pipeline.batch_size,
                "log_level": self.pipeline.log_level
            }
        }
