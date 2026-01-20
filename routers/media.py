"""
User media upload endpoints.
Handles audio and image uploads to S3 with database tracking.
"""
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from pathlib import Path

from database import get_db
from models import UserMedia, Profile
from schemas import UserMediaUploadResponse, UserMediaListResponse, MediaType
from utils.auth import get_current_user
from utils.s3_client import s3_client

router = APIRouter(prefix="/api/v1/media", tags=["User Media"])
logger = logging.getLogger(__name__)

# Allowed file extensions and MIME types
ALLOWED_AUDIO_EXTENSIONS = {'.mp3', '.wav', '.m4a', '.aac', '.ogg', '.flac'}
ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}

AUDIO_MIME_TYPES = {
    'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/x-wav', 
    'audio/mp4', 'audio/aac', 'audio/ogg', 'audio/flac'
}
IMAGE_MIME_TYPES = {
    'image/jpeg', 'image/png', 'image/webp', 'image/gif'
}

# File size limits (in bytes)
MAX_AUDIO_SIZE = 50 * 1024 * 1024  # 50 MB
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB


def validate_file(file: UploadFile, media_type: str) -> None:
    """
    Validate uploaded file based on media type.
    
    Args:
        file: The uploaded file
        media_type: Type of media (audio or image)
    
    Raises:
        HTTPException: If file is invalid
    """
    # Get file extension
    file_ext = Path(file.filename).suffix.lower()
    
    # Validate based on media type
    if media_type == MediaType.AUDIO:
        if file_ext not in ALLOWED_AUDIO_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid audio file format. Allowed: {', '.join(ALLOWED_AUDIO_EXTENSIONS)}"
            )
        if file.content_type not in AUDIO_MIME_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid audio MIME type: {file.content_type}"
            )
    
    elif media_type == MediaType.IMAGE:
        if file_ext not in ALLOWED_IMAGE_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid image file format. Allowed: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}"
            )
        if file.content_type not in IMAGE_MIME_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid image MIME type: {file.content_type}"
            )
    
    else:
        raise HTTPException(status_code=400, detail="Invalid media type")


@router.post("/upload/audio") #, response_model=UserMediaUploadResponse)
async def upload_audio(
    file: UploadFile = File(...),
    #user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload an audio file to S3.
    
    Supports: MP3, WAV, M4A, AAC, OGG, FLAC
    Max size: 50 MB
    """
    # Validate file
    validate_file(file, MediaType.AUDIO)
    
    # Check file size
    file_content = await file.read()
    file_size = len(file_content)
    
    if file_size > MAX_AUDIO_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_AUDIO_SIZE / 1024 / 1024} MB"
        )
    
    # Generate S3 key
    import uuid
    test_user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    file_ext = Path(file.filename).suffix.lower()
    s3_key = s3_client.generate_s3_key(
        user_id=str(test_user_id), #user.id
        media_type="audio",
        file_extension=file_ext
    )
    
    # Upload to S3
    from io import BytesIO
    file_obj = BytesIO(file_content)
    
    success, s3_url, error = s3_client.upload_file(
        file_obj=file_obj,
        s3_key=s3_key,
        content_type=file.content_type,
        metadata={
            'user_id': str(test_user_id), #user.id
            'original_filename': file.filename
        }
    )
    
    if not success:
        logger.error(f"Failed to upload audio to S3: {error}")
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {error}")
    
    # Create database entry
    # media_entry = UserMedia(
    #     user_id=test_user_id, #user.id
    #     media_type=MediaType.AUDIO,
    #     file_name=Path(s3_key).name,
    #     original_file_name=file.filename,
    #     s3_key=s3_key,
    #     s3_url=s3_url,
    #     file_size=file_size,
    #     mime_type=file.content_type,
    #     media_metadata={}
    # )
    
    # db.add(media_entry)
    # db.commit()
    # db.refresh(media_entry)
    
    # logger.info(f"User {test_user_id} uploaded audio file: {file.filename} -> {s3_key}")
    
    #return media_entry
    return {'status': 'success', 's3_url': s3_url}


@router.post("/upload/image") #, response_model=UserMediaUploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    #user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload an image file to S3.
    
    Supports: JPG, PNG, WebP, GIF
    Max size: 10 MB
    """
    # Validate file
    validate_file(file, MediaType.IMAGE)
    import uuid
    test_user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    
    # Check file size
    file_content = await file.read()
    file_size = len(file_content)
    
    if file_size > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_IMAGE_SIZE / 1024 / 1024} MB"
        )
    
    # Generate S3 key
    file_ext = Path(file.filename).suffix.lower()
    s3_key = s3_client.generate_s3_key(
        user_id=str(test_user_id), #user.id
        media_type="image",
        file_extension=file_ext
    )
    
    # Upload to S3
    from io import BytesIO
    file_obj = BytesIO(file_content)
    
    success, s3_url, error = s3_client.upload_file(
        file_obj=file_obj,
        s3_key=s3_key,
        content_type=file.content_type,
        media_metadata={
            'user_id': str(test_user_id), #user.id
            'original_filename': file.filename
        }
    )
    
    if not success:
        logger.error(f"Failed to upload image to S3: {error}")
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {error}")
    
    # Create database entry
    # media_entry = UserMedia(
    #     user_id=test_user_id, #user.id
    #     media_type=MediaType.IMAGE,
    #     file_name=Path(s3_key).name,
    #     original_file_name=file.filename,
    #     s3_key=s3_key,
    #     s3_url=s3_url,
    #     file_size=file_size,
    #     mime_type=file.content_type,
    #     media_metadata={}
    # )
    
    # db.add(media_entry)
    # db.commit()
    # db.refresh(media_entry)
    
    # logger.info(f"User {'testing-user'} uploaded image file: {file.filename} -> {s3_key}")
    
    # return media_entry
    return {'status': 'success', 's3_url': s3_url}


@router.get("/list", response_model=List[UserMediaListResponse])
async def list_user_media(
    media_type: Optional[str] = Query(None, description="Filter by media type (audio or image)"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    #user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all media files uploaded by the current user.
    
    Optional filters:
    - media_type: Filter by 'audio' or 'image'
    - limit: Maximum items per page (default: 50, max: 100)
    - offset: Pagination offset (default: 0)
    """
    query = db.query(UserMedia).filter(UserMedia.user_id == 'testing-user')
    
    # Apply media type filter if provided
    if media_type:
        if media_type not in [MediaType.AUDIO, MediaType.IMAGE]:
            raise HTTPException(status_code=400, detail="Invalid media_type. Use 'audio' or 'image'")
        query = query.filter(UserMedia.media_type == media_type)
    
    # Order by most recent first
    query = query.order_by(UserMedia.created_at.desc())
    
    # Apply pagination
    media_list = query.offset(offset).limit(limit).all()
    
    return media_list


@router.get("/{media_id}", response_model=UserMediaListResponse)
async def get_media_by_id(
    media_id: str,
    user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get details of a specific media file by ID.
    """
    media = db.query(UserMedia).filter(
        UserMedia.id == media_id,
        UserMedia.user_id == user.id
    ).first()
    
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    
    return media


@router.delete("/{media_id}")
async def delete_media(
    media_id: str,
    user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a media file from S3 and database.
    """
    # Find the media entry
    media = db.query(UserMedia).filter(
        UserMedia.id == media_id,
        UserMedia.user_id == user.id
    ).first()
    
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    
    # Delete from S3
    success, error = s3_client.delete_file(media.s3_key)
    
    if not success:
        logger.warning(f"Failed to delete file from S3: {error}")
        # Continue with database deletion even if S3 deletion fails
    
    # Delete from database
    db.delete(media)
    db.commit()
    
    logger.info(f"User {user.id} deleted media {media_id}: {media.file_name}")
    
    return {
        "message": "Media deleted successfully",
        "id": str(media.id),
        "file_name": media.file_name
    }
