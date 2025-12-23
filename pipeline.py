#!/usr/bin/env python3
"""
Bono AI Fashion Catalog Pipeline
=================================

Main automation script that orchestrates:
1. Watching Google Drive for new garment images
2. Processing images through RunPod + ComfyUI
3. Generating PDF catalogs
4. Uploading outputs back to Google Drive

Usage:
    # Run a single batch
    python pipeline.py batch --input ./input --output ./output
    
    # Watch Google Drive for new batches
    python pipeline.py watch
    
    # Generate PDF from existing images
    python pipeline.py catalog --images ./generated --output catalog.pdf
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import json
import threading

import click
from dotenv import load_dotenv
from tqdm import tqdm

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import Config
from src.generators import TeenBoyGenerator, BaseGenerator
from src.generators.infant import InfantGenerator
from src.integrations import RunPodClient, GoogleDriveClient
from src.catalog import CatalogAssembler
from src.utils import setup_logging, ImageProcessor
from src.utils.logging import get_logger


# Category to Generator mapping (for future expansion)
GENERATORS = {
    "teen_boy": TeenBoyGenerator,
    "infant": InfantGenerator,
    # Future: "teen_girl": TeenGirlGenerator,
    # Future: "women": WomenGenerator,
}


class FashionCatalogPipeline:
    """
    Main pipeline orchestrator.
    
    Coordinates the flow from input images through AI generation
    to PDF catalog output.
    
    Example:
        pipeline = FashionCatalogPipeline()
        await pipeline.run_batch("./input", "./output")
    """
    
    def __init__(
        self,
        config: Optional[Config] = None,
        workflow_path: str = "./workflow_api.json"
    ):
        """
        Initialize the pipeline.
        
        Args:
            config: Optional configuration (loads from env if not provided)
            workflow_path: Path to ComfyUI workflow JSON
        """
        self.config = config or Config.from_env()
        self.workflow_path = workflow_path
        self.logger = get_logger("pipeline")
        
        # Initialize clients
        self.runpod = RunPodClient(
            api_key=self.config.runpod.api_key,
            endpoint_id=self.config.runpod.endpoint_id,
            timeout=self.config.runpod.timeout,
            poll_interval=self.config.runpod.poll_interval
        )
        
        self.drive: Optional[GoogleDriveClient] = None
        
        # Initialize generator based on category
        self.generator = self._create_generator()
        
        # Initialize catalog assembler
        self.assembler = CatalogAssembler(
            brand=self.config.pipeline.brand.upper(),
            logo_path=str(self.config.pipeline.assets_dir / "logos" / "bono.png")
        )
        
        # Image processor
        self.image_processor = ImageProcessor()
    
    def _create_generator(self) -> BaseGenerator:
        """Create the appropriate generator based on config."""
        category = self.config.pipeline.category
        
        if category not in GENERATORS:
            self.logger.warning(
                f"Unknown category '{category}', defaulting to teen_boy"
            )
            category = "teen_boy"
        
        generator_class = GENERATORS[category]
        return generator_class(self.runpod)
    
    def init_google_drive(self):
        """Initialize Google Drive client (requires OAuth)."""
        self.drive = GoogleDriveClient(
            credentials_path=self.config.google_drive.credentials_path
        )
        self.drive.authenticate()
    
    async def process_single_garment(
        self,
        garment_path: str,
        output_dir: str
    ) -> Dict[str, Any]:
        """
        Process a single garment image.
        
        Args:
            garment_path: Path to garment image
            output_dir: Directory for outputs
            
        Returns:
            dict: Processing result with output paths
        """
        self.logger.info("Processing garment", path=garment_path)
        
        # Prepare the garment image
        prepared_path = str(Path(output_dir) / "temp" / Path(garment_path).name)
        self.image_processor.prepare_garment_image(garment_path, prepared_path)
        
        # Load workflow
        workflow = self._load_workflow()
        
        # Inject garment image and prompts
        workflow = self._configure_workflow(workflow, prepared_path)
        
        # Submit to RunPod
        result = await self.runpod.submit_workflow_with_images(
            workflow_path=self.workflow_path,
            garment_image_path=prepared_path,
            output_dir=output_dir
        )
        
        if result.get("success"):
            # Create closeup from full body
            if result.get("full_body_path"):
                closeup_path = str(
                    Path(output_dir) / 
                    f"closeup_{Path(garment_path).stem}.png"
                )
                self.image_processor.create_closeup(
                    result["full_body_path"],
                    closeup_path,
                    focus_region="upper"
                )
                result["closeup_path"] = closeup_path
        
        return result
    
    async def run_batch(
        self,
        input_dir: str,
        output_dir: str,
        generate_pdf: bool = True
    ) -> Dict[str, Any]:
        """
        Process a batch of garment images.
        
        Args:
            input_dir: Directory containing garment images
            output_dir: Directory for outputs
            generate_pdf: Whether to generate PDF catalog
            
        Returns:
            dict: Batch processing results
        """
        self.logger.info("Starting batch processing", input=input_dir, output=output_dir)
        
        # Find all images
        input_path = Path(input_dir)
        image_files = []
        for ext in ImageProcessor.SUPPORTED_FORMATS:
            image_files.extend(input_path.glob(f"*{ext}"))
            image_files.extend(input_path.glob(f"*{ext.upper()}"))
        
        if not image_files:
            self.logger.warning("No images found", directory=input_dir)
            return {"success": False, "error": "No images found"}
        
        self.logger.info("Found images", count=len(image_files))
        
        # Create output directories
        output_path = Path(output_dir)
        images_dir = output_path / "HighRes_Images"
        images_dir.mkdir(parents=True, exist_ok=True)
        
        # Process each garment
        results = []
        for garment_path in tqdm(image_files, desc="Processing garments"):
            try:
                result = await self.process_single_garment(
                    str(garment_path),
                    str(images_dir)
                )
                result["garment_name"] = garment_path.stem
                results.append(result)
            except Exception as e:
                self.logger.error(
                    "Failed to process garment",
                    path=str(garment_path),
                    error=str(e)
                )
                results.append({
                    "success": False,
                    "error": str(e),
                    "garment_name": garment_path.stem
                })
        
        # Generate PDF catalog
        pdf_path = None
        if generate_pdf:
            successful_results = [r for r in results if r.get("success")]
            if successful_results:
                pdf_path = str(output_path / f"Final_Catalog_{self.config.pipeline.brand}.pdf")
                self.assembler.create_catalog(
                    images=successful_results,
                    output_path=pdf_path
                )
        
        return {
            "success": True,
            "total": len(image_files),
            "processed": len([r for r in results if r.get("success")]),
            "failed": len([r for r in results if not r.get("success")]),
            "pdf_path": pdf_path,
            "images_dir": str(images_dir),
            "results": results
        }
    
    def watch_drive(
        self,
        poll_interval: int = 60
    ):
        """
        Watch Google Drive for new batches.
        
        Args:
            poll_interval: Seconds between polls
        """
        if not self.drive:
            self.init_google_drive()
        
        stop_event = threading.Event()
        
        def on_new_files(files):
            """Callback when new files are detected."""
            self.logger.info("New files detected", count=len(files))
            
            # Download files
            temp_dir = str(self.config.pipeline.temp_dir / "downloads")
            downloaded = self.drive.download_batch(files, temp_dir)
            
            # Process batch
            output_dir = str(self.config.pipeline.output_dir / "latest_batch")
            
            # Run async processing
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    self.run_batch(temp_dir, output_dir)
                )
            finally:
                loop.close()
            
            # Upload results
            if result.get("success") and result.get("pdf_path"):
                self.drive.upload_file(
                    result["pdf_path"],
                    self.config.google_drive.output_folder_id
                )
                
                # Upload high-res images folder
                if result.get("images_dir"):
                    for img_path in Path(result["images_dir"]).glob("*.png"):
                        self.drive.upload_file(
                            str(img_path),
                            self.config.google_drive.output_folder_id
                        )
            
            self.logger.info("Batch complete", result=result)
        
        self.logger.info(
            "Starting Drive watcher",
            folder_id=self.config.google_drive.input_folder_id
        )
        
        try:
            self.drive.watch_folder(
                folder_id=self.config.google_drive.input_folder_id,
                callback=on_new_files,
                poll_interval=poll_interval,
                stop_event=stop_event
            )
        except KeyboardInterrupt:
            self.logger.info("Stopping watcher...")
            stop_event.set()
    
    def _load_workflow(self) -> Dict[str, Any]:
        """Load the ComfyUI workflow."""
        with open(self.workflow_path, 'r') as f:
            return json.load(f)
    
    def _configure_workflow(
        self,
        workflow: Dict[str, Any],
        garment_path: str
    ) -> Dict[str, Any]:
        """Configure workflow with generator settings."""
        # Get prompts from generator
        positive_prompt = self.generator.get_model_prompt()
        negative_prompt = self.generator.get_negative_prompt()
        vto_config = self.generator.get_vto_config()
        
        # These would be updated based on actual workflow structure
        # For now, return with embedded settings
        workflow["config"] = {
            "positive_prompt": positive_prompt,
            "negative_prompt": negative_prompt,
            "garment_path": garment_path,
            "vto_config": vto_config,
            "overrides": self.generator.get_workflow_overrides()
        }
        
        return workflow
    
    def generate_catalog_from_images(
        self,
        images_dir: str,
        output_path: str
    ) -> str:
        """
        Generate PDF catalog from existing images.
        
        Args:
            images_dir: Directory containing generated images
            output_path: Output PDF path
            
        Returns:
            str: Path to generated PDF
        """
        self.logger.info("Generating catalog from images", directory=images_dir)
        
        # Find all images
        image_path = Path(images_dir)
        images = []
        
        for img_file in sorted(image_path.glob("*.png")):
            images.append({
                "full_body": str(img_file),
                "product_name": img_file.stem.replace("_", " ").title()
            })
        
        if not images:
            raise ValueError(f"No images found in {images_dir}")
        
        return self.assembler.create_catalog(images, output_path)


# CLI Commands
@click.group()
@click.option('--debug', is_flag=True, help='Enable debug logging')
def cli(debug):
    """Bono AI Fashion Catalog Pipeline CLI."""
    load_dotenv()
    setup_logging(level="DEBUG" if debug else "INFO")


@cli.command()
@click.option('--input', '-i', required=True, help='Input directory with garment images')
@click.option('--output', '-o', required=True, help='Output directory')
@click.option('--no-pdf', is_flag=True, help='Skip PDF generation')
def batch(input, output, no_pdf):
    """Process a batch of garment images."""
    pipeline = FashionCatalogPipeline()
    
    result = asyncio.run(
        pipeline.run_batch(input, output, generate_pdf=not no_pdf)
    )
    
    if result.get("success"):
        click.echo(f"✅ Batch complete!")
        click.echo(f"   Processed: {result['processed']}/{result['total']}")
        if result.get("pdf_path"):
            click.echo(f"   PDF: {result['pdf_path']}")
    else:
        click.echo(f"❌ Batch failed: {result.get('error')}")
        sys.exit(1)


@cli.command()
@click.option('--poll-interval', default=60, help='Seconds between Drive polls')
def watch(poll_interval):
    """Watch Google Drive for new batches."""
    click.echo("Starting Google Drive watcher...")
    click.echo("Press Ctrl+C to stop")
    
    pipeline = FashionCatalogPipeline()
    pipeline.watch_drive(poll_interval=poll_interval)


@cli.command()
@click.option('--images', '-i', required=True, help='Directory with generated images')
@click.option('--output', '-o', required=True, help='Output PDF path')
def catalog(images, output):
    """Generate PDF catalog from existing images."""
    pipeline = FashionCatalogPipeline()
    
    try:
        pdf_path = pipeline.generate_catalog_from_images(images, output)
        click.echo(f"✅ Catalog generated: {pdf_path}")
    except Exception as e:
        click.echo(f"❌ Failed: {e}")
        sys.exit(1)


@cli.command()
def validate():
    """Validate configuration and connections."""
    click.echo("Validating configuration...")
    
    try:
        config = Config.from_env()
        config.validate()
        click.echo("✅ Configuration valid")
    except ValueError as e:
        click.echo(f"❌ Configuration error: {e}")
        sys.exit(1)
    
    # Check workflow file
    if os.path.exists("./workflow_api.json"):
        click.echo("✅ Workflow file found")
    else:
        click.echo("⚠️  workflow_api.json not found")
    
    # Check assets
    logo_path = Path("./assets/logos/bono.png")
    if logo_path.exists():
        click.echo("✅ Brand logo found")
    else:
        click.echo("⚠️  Brand logo not found (optional)")


if __name__ == "__main__":
    cli()
