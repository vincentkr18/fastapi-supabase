"""
User profile endpoints.
Authenticated users can view and update their own profile.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated
from uuid import UUID

from database import get_db
from models import Video, Tag
from schemas import VideoOut
from fastapi import APIRouter, Depends, Query
from typing import List
from pydantic import BaseModel

router = APIRouter(prefix="/templates", tags=["Templates"])


class VideoListResponse(BaseModel):
    page: int
    limit: int
    total: int
    items: List[VideoOut]


@router.get("/videos", response_model=VideoListResponse)
def list_videos(
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=100),
    search: str | None = None,
    tags: str | None = None,
    db: Session = Depends(get_db)
):
    query = db.query(Video)

    if search:
        query = query.filter(Video.title.ilike(f"%{search}%"))

    if tags:
        tag_list = tags.split(",")
        query = query.join(Video.tags).filter(Tag.name.in_(tag_list))

    total = query.distinct().count()

    videos = (
        query.distinct()
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return VideoListResponse(
        page=page,
        limit=limit,
        total=total,
        items=[VideoOut.model_validate(video) for video in videos]
    )
