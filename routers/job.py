from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from pathlib import Path

from database import get_db
from models import GenerationJob
from schemas import JobStatusResponse, JobStatus

router = APIRouter(prefix="/api/v1/jobs", tags=["Jobs"])

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)


@router.get("/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """Get job status with progress percentage"""
    job = db.query(GenerationJob).filter(GenerationJob.job_id == job_id).first()
    
    if not job:
        raise HTTPException(404, "Job not found")
    
    video_url = None
    if job.status == JobStatus.COMPLETED.value and job.output_video_path:
        video_url = f"/api/v1/jobs/{job_id}/download"
    
    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        progress=job.progress,
        video_url=video_url,
        error=job.error_message,
        created_at=job.created_at,
        updated_at=job.updated_at
    )


@router.get("/{job_id}/download")
async def download_video(job_id: str, db: Session = Depends(get_db)):
    """Download generated video - returns file directly (not base64)"""
    job = db.query(GenerationJob).filter(GenerationJob.job_id == job_id).first()
    
    if not job:
        raise HTTPException(404, "Job not found")
    
    if job.status != JobStatus.COMPLETED.value:
        raise HTTPException(400, "Video not ready yet")
    
    if not job.output_video_path or not Path(job.output_video_path).exists():
        raise HTTPException(404, "Video file not found")
    
    return FileResponse(
        path=job.output_video_path,
        media_type="video/mp4",
        filename=f"generated_{job_id}.mp4"
    )


@router.get("/{job_id}/stream")
async def stream_video(job_id: str, db: Session = Depends(get_db)):
    """Stream video for in-browser playback"""
    job = db.query(GenerationJob).filter(GenerationJob.job_id == job_id).first()
    
    if not job:
        raise HTTPException(404, "Job not found")
    
    if job.status != JobStatus.COMPLETED.value:
        raise HTTPException(400, "Video not ready")
    
    if not job.output_video_path or not Path(job.output_video_path).exists():
        raise HTTPException(404, "Video file not found")
    
    def iterfile():
        with open(job.output_video_path, mode="rb") as file_like:
            yield from file_like
    
    return StreamingResponse(iterfile(), media_type="video/mp4")