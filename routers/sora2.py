from fastapi import APIRouter, File, UploadFile, Form, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from typing import Optional
from pathlib import Path
import uuid
from loguru import logger

from database import get_db
from models import GenerationJob, Video
from schemas import JobResponse, AspectRatio, VideoModel, JobStatus
import random

router = APIRouter(prefix="/api/v1/sora-2", tags=["Sora 2"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


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
async def create_sora2_video(
    background_tasks: BackgroundTasks,
    aspect_ratio: AspectRatio = Form(...),
    prompt: str = Form(...),
    character_description: Optional[str] = Form(None),
    environment_description: Optional[str] = Form(None),
    gestures: Optional[str] = Form(None),
    dialogue: Optional[str] = Form(None),
    voice_tone: Optional[str] = Form(None),
    product_image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Generate video using Sora 2
    - prompt: Text description
    - product_image: Upload image file (multipart/form-data)
    """
    logger.info("=" * 80)
    logger.info("SORA 2 REQUEST RECEIVED")
    logger.info(f"Aspect Ratio: {aspect_ratio}")
    logger.info(f"Prompt: {prompt}")
    logger.info(f"Character Description: {character_description}")
    logger.info(f"Environment Description: {environment_description}")
    logger.info(f"Gestures: {gestures}")
    logger.info(f"Dialogue: {dialogue}")
    logger.info(f"Voice Tone: {voice_tone}")
    logger.info(f"Product Image: {product_image.filename if product_image else 'None'}")
    logger.info(f"Product Image Size: {product_image.size if product_image else 'N/A'} bytes")
    logger.info("=" * 80)
    
    job_id = str(uuid.uuid4())
    job_dir = UPLOAD_DIR / job_id
    job_dir.mkdir(exist_ok=True)
    
    image_path = None
    
    # Handle product image
    if product_image:
        if not validate_file_extension(product_image.filename, ALLOWED_IMAGE_EXTENSIONS):
            raise HTTPException(400, f"Invalid image format. Allowed: {ALLOWED_IMAGE_EXTENSIONS}")
        
        if not validate_file_size(product_image, MAX_IMAGE_SIZE):
            raise HTTPException(413, "Image too large. Max 10MB")
        
        image_path = job_dir / f"product_{product_image.filename}"
        await save_upload_file(product_image, image_path)
    
    # Create job
    new_job = GenerationJob(
        job_id=job_id,
        model_type=VideoModel.SORA_2.value,
        aspect_ratio=aspect_ratio.value,
        prompt=prompt,
        character_description=character_description,
        environment_description=environment_description,
        gestures=gestures,
        dialogue=dialogue,
        voice_tone=voice_tone,
        product_image_path=str(image_path) if image_path else None,
        status=JobStatus.PENDING.value,
        progress=0
    )
    
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    
    # Get random video from Video table
    videos = db.query(Video).all()
    random_video_url = random.choice(videos).video_url if videos else "https://res.cloudinary.com/demo/video/upload/sample_video.mp4"
    
    logger.info(f"Selected random video URL: {random_video_url}")
    
    # TODO: Add background task for actual video generation
    # background_tasks.add_task(process_sora2, job_id, db)
    
    return JobResponse(
        job_id=job_id,
        status=new_job.status,
        model=new_job.model_type,
        progress=new_job.progress,
        created_at=new_job.created_at,
        video_generated_path=random_video_url
    )