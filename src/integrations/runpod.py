"""
RunPod API Integration for ComfyUI Workflow Execution.

This module provides an async client for submitting ComfyUI workflows
to RunPod serverless endpoints and retrieving results.
"""

import asyncio
import base64
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
import structlog

logger = structlog.get_logger()


@dataclass
class JobResult:
    """Result of a RunPod job."""
    success: bool
    job_id: str
    status: str
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None


class RunPodClient:
    """
    Async client for RunPod Serverless API.
    
    Handles submission of ComfyUI workflows and polling for results.
    
    Example:
        client = RunPodClient(api_key="...", endpoint_id="...")
        result = await client.submit_job(workflow, images={"garment": "base64..."})
    """
    
    BASE_URL = "https://api.runpod.ai/v2"
    
    def __init__(
        self,
        api_key: str,
        endpoint_id: str,
        timeout: int = 300,
        poll_interval: int = 5
    ):
        """
        Initialize the RunPod client.
        
        Args:
            api_key: RunPod API key
            endpoint_id: Serverless endpoint ID
            timeout: Maximum time to wait for job completion (seconds)
            poll_interval: Time between status polls (seconds)
        """
        self.api_key = api_key
        self.endpoint_id = endpoint_id
        self.timeout = timeout
        self.poll_interval = poll_interval
        self.base_url = f"{self.BASE_URL}/{endpoint_id}"
        
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def submit_job(
        self,
        workflow: Dict[str, Any],
        images: Optional[Dict[str, str]] = None,
        wait_for_completion: bool = True
    ) -> JobResult:
        """
        Submit a ComfyUI workflow job.
        
        Args:
            workflow: ComfyUI workflow definition (API format)
            images: Optional dict of image name -> base64 encoded image
            wait_for_completion: Whether to wait for job to complete
            
        Returns:
            JobResult: The result of the job
        """
        start_time = time.time()
        
        payload = {
            "input": {
                "workflow": workflow,
            }
        }
        
        if images:
            payload["input"]["images"] = images
        
        async with httpx.AsyncClient(timeout=30) as client:
            # Submit job
            response = await client.post(
                f"{self.base_url}/run",
                headers=self.headers,
                json=payload
            )
            
            if response.status_code != 200:
                return JobResult(
                    success=False,
                    job_id="",
                    status="error",
                    error=f"Failed to submit job: {response.text}"
                )
            
            data = response.json()
            job_id = data.get("id")
            
            logger.info("Job submitted", job_id=job_id)
            
            if not wait_for_completion:
                return JobResult(
                    success=True,
                    job_id=job_id,
                    status="queued"
                )
            
            # Poll for completion
            result = await self._poll_for_result(client, job_id)
            result.execution_time = time.time() - start_time
            return result
    
    async def _poll_for_result(
        self,
        client: httpx.AsyncClient,
        job_id: str
    ) -> JobResult:
        """Poll for job completion."""
        start_time = time.time()
        
        while True:
            if time.time() - start_time > self.timeout:
                return JobResult(
                    success=False,
                    job_id=job_id,
                    status="timeout",
                    error=f"Job timed out after {self.timeout} seconds"
                )
            
            response = await client.get(
                f"{self.base_url}/status/{job_id}",
                headers=self.headers
            )
            
            if response.status_code != 200:
                await asyncio.sleep(self.poll_interval)
                continue
            
            data = response.json()
            status = data.get("status")
            
            logger.debug("Job status", job_id=job_id, status=status)
            
            if status == "COMPLETED":
                return JobResult(
                    success=True,
                    job_id=job_id,
                    status=status,
                    output=data.get("output", {})
                )
            
            if status == "FAILED":
                return JobResult(
                    success=False,
                    job_id=job_id,
                    status=status,
                    error=data.get("error", "Job failed without error message")
                )
            
            if status == "CANCELLED":
                return JobResult(
                    success=False,
                    job_id=job_id,
                    status=status,
                    error="Job was cancelled"
                )
            
            await asyncio.sleep(self.poll_interval)
    
    async def get_job_status(self, job_id: str) -> JobResult:
        """Get the current status of a job."""
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{self.base_url}/status/{job_id}",
                headers=self.headers
            )
            
            if response.status_code != 200:
                return JobResult(
                    success=False,
                    job_id=job_id,
                    status="error",
                    error=f"Failed to get status: {response.text}"
                )
            
            data = response.json()
            return JobResult(
                success=data.get("status") == "COMPLETED",
                job_id=job_id,
                status=data.get("status"),
                output=data.get("output"),
                error=data.get("error")
            )
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job."""
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self.base_url}/cancel/{job_id}",
                headers=self.headers
            )
            return response.status_code == 200
    
    @staticmethod
    def encode_image(image_path: str) -> str:
        """Encode an image file to base64."""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    
    @staticmethod
    def decode_image(base64_str: str, output_path: str) -> str:
        """Decode a base64 image and save to file."""
        image_data = base64.b64decode(base64_str)
        with open(output_path, "wb") as f:
            f.write(image_data)
        return output_path
    
    async def submit_workflow_with_images(
        self,
        workflow_path: str,
        garment_image_path: str,
        output_dir: str
    ) -> Dict[str, Any]:
        """
        High-level helper to submit a workflow with garment image.
        
        Args:
            workflow_path: Path to workflow JSON file
            garment_image_path: Path to garment image
            output_dir: Directory to save output images
            
        Returns:
            dict: Result with output paths
        """
        # Load workflow
        with open(workflow_path, "r") as f:
            workflow = json.load(f)
        
        # Encode input image
        garment_b64 = self.encode_image(garment_image_path)
        
        # Submit job
        result = await self.submit_job(
            workflow=workflow,
            images={"garment": garment_b64}
        )
        
        if not result.success:
            return {
                "success": False,
                "error": result.error
            }
        
        # Decode and save output images
        output_paths = {}
        output = result.output or {}
        
        if "full_body" in output:
            path = Path(output_dir) / f"full_body_{result.job_id}.png"
            self.decode_image(output["full_body"], str(path))
            output_paths["full_body_path"] = str(path)
        
        if "closeup" in output:
            path = Path(output_dir) / f"closeup_{result.job_id}.png"
            self.decode_image(output["closeup"], str(path))
            output_paths["closeup_path"] = str(path)
        
        if "final" in output:
            path = Path(output_dir) / f"final_{result.job_id}.png"
            self.decode_image(output["final"], str(path))
            output_paths["output_path"] = str(path)
        
        return {
            "success": True,
            "job_id": result.job_id,
            **output_paths
        }
