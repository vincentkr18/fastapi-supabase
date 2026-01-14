from fastapi import APIRouter, File, UploadFile, Form, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from typing import Optional
from pathlib import Path
import uuid
from datetime import datetime
from loguru import logger
import os

from database import get_db
from models import GenerationJob, Video
from schemas import JobResponse, AspectRatio, VideoModel, JobStatus

router = APIRouter(prefix="/api/v1/lip-sync", tags=["Lip Sync"])

# Use /tmp for serverless environments
if os.environ.get('VERCEL') or os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
    UPLOAD_DIR = Path("/tmp/uploads")
else:
    UPLOAD_DIR = Path("uploads")

try:
    UPLOAD_DIR.mkdir(exist_ok=True, parents=True)
except OSError:
    pass

MAX_AUDIO_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg", ".flac"}


def validate_file_size(file: UploadFile, max_size: int) -> bool:
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    return file_size <= max_size


def validate_file_extension(filename: str, allowed_extensions: set) -> bool:
    ext = Path(filename).suffix.lower()
    return ext in allowed_extensions


async def save_upload_file(upload_file: UploadFile, destination: Path) -> Path:
    with open(destination, 'wb') as buffer:
        content = await upload_file.read()
        buffer.write(content)
    return destination


@router.post("", response_model=JobResponse)
async def create_lip_sync_video(
    background_tasks: BackgroundTasks,
    aspect_ratio: AspectRatio = Form(...),
    video_template_id: int = Form(...),
    text_input: Optional[str] = Form(None),
    voice_id: Optional[str] = Form(None),
    audio_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Create Lip Sync video
    - video_template_id: References Video table (Cloudinary URL)
    - audio_file: Upload audio file (multipart/form-data)
    - OR text_input + voice_id: For ElevenLabs TTS
    """
    logger.info("=" * 80)
    logger.info("LIP SYNC REQUEST RECEIVED")
    logger.info(f"Aspect Ratio: {aspect_ratio}")
    logger.info(f"Video Template ID: {video_template_id}")
    logger.info(f"Text Input: {text_input}")
    logger.info(f"Voice ID: {voice_id}")
    logger.info(f"Audio File: {audio_file.filename if audio_file else 'None'}")
    logger.info(f"Audio File Size: {audio_file.size if audio_file else 'N/A'} bytes")
    logger.info("=" * 80)
    
    # Validation
    if not audio_file and not text_input:
        raise HTTPException(400, "Either audio_file or text_input is required")
    
    if text_input and not voice_id:
        raise HTTPException(400, "voice_id required with text_input")
    
    # Verify video template exists
    video_template = db.query(Video).filter(Video.id == video_template_id).first()
    if not video_template:
        raise HTTPException(404, "Video template not found")
    
    # Create job directory
    job_id = str(uuid.uuid4())
    job_dir = UPLOAD_DIR / job_id
    job_dir.mkdir(exist_ok=True)
    
    audio_path = None
    
    # Handle audio file
    if audio_file:
        if not validate_file_extension(audio_file.filename, ALLOWED_AUDIO_EXTENSIONS):
            raise HTTPException(400, f"Invalid audio format. Allowed: {ALLOWED_AUDIO_EXTENSIONS}")
        
        if not validate_file_size(audio_file, MAX_AUDIO_SIZE):
            raise HTTPException(413, "Audio file too large. Max 10MB")
        
        audio_path = job_dir / f"audio_{audio_file.filename}"
        await save_upload_file(audio_file, audio_path)
    
    # Create job
    new_job = GenerationJob(
        job_id=job_id,
        model_type=VideoModel.LIP_SYNC.value,
        aspect_ratio=aspect_ratio.value,
        video_template_id=video_template_id,
        audio_file_path=str(audio_path) if audio_path else None,
        text_input=text_input,
        voice_id=voice_id,
        status=JobStatus.PENDING.value,
        progress=0
    )
    
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    
    # TODO: Add background task for actual video generation
    # background_tasks.add_task(process_lip_sync, job_id, db)
    
    return JobResponse(
        job_id=job_id,
        status=new_job.status,
        model=new_job.model_type,
        progress=new_job.progress,
        created_at=new_job.created_at,
        video_generated_path=video_template.video_url
    )