"""
Bono Catalog API - FastAPI Backend

This API handles:
- AI model generation via RunPod
- PDF catalog creation
- Google Drive uploads
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Config
from src.generators import TeenBoyGenerator
from src.integrations import RunPodClient, GoogleDriveClient
from src.catalog import CatalogAssembler
from src.utils import setup_logging

# Initialize
setup_logging()
app = FastAPI(title="Bono Catalog API", version="1.0.0")

# CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://*.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load config
config = Config.from_env()


class GenerateRequest(BaseModel):
    jobId: str
    metadata: dict


class CatalogRequest(BaseModel):
    jobId: str


class DriveUploadRequest(BaseModel):
    pdfUrl: Optional[str] = None
    jobId: Optional[str] = None


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.post("/generate")
async def generate(request: GenerateRequest, background_tasks: BackgroundTasks):
    """
    Start AI generation for the given job.
    This runs in the background and updates job metadata.
    """
    background_tasks.add_task(run_generation, request.jobId, request.metadata)
    return {"status": "started", "jobId": request.jobId}


async def run_generation(job_id: str, metadata: dict):
    """Background task to run AI generation."""
    job_dir = Path("temp") / job_id
    metadata_path = job_dir / "metadata.json"
    
    try:
        # Update status
        metadata["status"] = "generating"
        metadata["statusMessage"] = "Starting AI model generation..."
        metadata_path.write_text(json.dumps(metadata, indent=2))
        
        # Initialize RunPod client
        runpod = RunPodClient(
            api_key=config.runpod.api_key,
            endpoint_id=config.runpod.endpoint_id
        )
        
        # Initialize generator
        generator = TeenBoyGenerator(runpod)
        
        # Process each garment image
        generated_images = []
        total = len(metadata.get("images", []))
        
        for i, image_info in enumerate(metadata.get("images", [])):
            metadata["currentItem"] = i + 1
            metadata["progress"] = int((i / total) * 100) if total > 0 else 0
            metadata["statusMessage"] = f"Generating model for {image_info['name']}..."
            metadata_path.write_text(json.dumps(metadata, indent=2))
            
            # Generate AI model with garment
            result = await generator.process(image_info["path"])
            
            if result.success:
                generated_images.append({
                    "garmentName": image_info["name"],
                    "fullBody": result.full_body_path or result.output_path,
                    "closeup": result.closeup_path,
                })
        
        # Update metadata with generated images
        metadata["generatedImages"] = generated_images
        metadata["status"] = "complete"
        metadata["progress"] = 100
        metadata["statusMessage"] = "Generation complete!"
        metadata_path.write_text(json.dumps(metadata, indent=2))
        
    except Exception as e:
        metadata["status"] = "error"
        metadata["error"] = str(e)
        metadata["statusMessage"] = f"Error: {str(e)}"
        metadata_path.write_text(json.dumps(metadata, indent=2))


@app.post("/catalog")
async def create_catalog(request: CatalogRequest):
    """Generate PDF catalog for a completed job."""
    job_dir = Path("temp") / request.jobId
    metadata_path = job_dir / "metadata.json"
    
    if not metadata_path.exists():
        raise HTTPException(status_code=404, detail="Job not found")
    
    metadata = json.loads(metadata_path.read_text())
    
    # Initialize assembler
    logo_path = metadata.get("logoPath") or str(Path("assets/logos/bono.png"))
    assembler = CatalogAssembler(
        brand=metadata.get("brandName", "BONO"),
        logo_path=logo_path if Path(logo_path).exists() else None
    )
    
    # Update assembler config
    assembler.config.tagline = metadata.get("tagline", "")
    assembler.config.catalog_title = metadata.get("collectionTitle", "Collection 2024")
    
    # Prepare images for catalog
    images = []
    for gen_img in metadata.get("generatedImages", []):
        images.append({
            "full_body": gen_img.get("fullBody"),
            "closeup": gen_img.get("closeup"),
            "product_name": gen_img.get("garmentName", "").replace("_", " ").title(),
        })
    
    # If no generated images, use original garment images as fallback
    if not images and metadata.get("images"):
        for img_info in metadata["images"]:
            images.append({
                "full_body": img_info["path"],
                "product_name": img_info["name"].replace("_", " ").title(),
            })
    
    # Generate PDF
    output_path = str(job_dir / f"catalog_{request.jobId[:8]}.pdf")
    assembler.create_catalog(images, output_path)
    
    # Update metadata
    metadata["pdfPath"] = output_path
    metadata_path.write_text(json.dumps(metadata, indent=2))
    
    return {
        "success": True,
        "pdfUrl": f"/download/{request.jobId}",
        "pdfPath": output_path,
    }


@app.get("/download/{job_id}")
async def download_pdf(job_id: str):
    """Download the generated PDF catalog."""
    job_dir = Path("temp") / job_id
    metadata_path = job_dir / "metadata.json"
    
    if not metadata_path.exists():
        raise HTTPException(status_code=404, detail="Job not found")
    
    metadata = json.loads(metadata_path.read_text())
    pdf_path = metadata.get("pdfPath")
    
    if not pdf_path or not Path(pdf_path).exists():
        raise HTTPException(status_code=404, detail="PDF not found")
    
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"catalog_{job_id[:8]}.pdf"
    )


@app.post("/drive/upload")
async def upload_to_drive(request: DriveUploadRequest):
    """Upload the catalog PDF to Google Drive."""
    if not request.jobId:
        raise HTTPException(status_code=400, detail="jobId required")
    
    job_dir = Path("temp") / request.jobId
    metadata_path = job_dir / "metadata.json"
    
    if not metadata_path.exists():
        raise HTTPException(status_code=404, detail="Job not found")
    
    metadata = json.loads(metadata_path.read_text())
    pdf_path = metadata.get("pdfPath")
    
    if not pdf_path or not Path(pdf_path).exists():
        raise HTTPException(status_code=404, detail="PDF not found")
    
    try:
        # Initialize Drive client
        drive = GoogleDriveClient(
            credentials_path=config.google_drive.credentials_path
        )
        drive.authenticate()
        
        # Upload to Drive
        file_id = drive.upload_file(
            pdf_path,
            config.google_drive.output_folder_id,
            file_name=f"Catalog_{metadata.get('brandName', 'Bono')}_{request.jobId[:8]}.pdf"
        )
        
        drive_url = f"https://drive.google.com/file/d/{file_id}/view"
        
        # Update metadata
        metadata["driveFileId"] = file_id
        metadata["driveUrl"] = drive_url
        metadata_path.write_text(json.dumps(metadata, indent=2))
        
        return {
            "success": True,
            "fileId": file_id,
            "driveUrl": drive_url,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
