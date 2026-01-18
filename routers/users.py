"""
User profile endpoints.
Authenticated users can view and update their own profile.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated
from uuid import UUID

from database import get_db
from models import Profile
from schemas import ProfileResponse, ProfileUpdate, MessageResponse
from utils.auth import get_current_user_id, get_current_user
from utils.supabase_client import get_supabase_client

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=ProfileResponse)
async def get_current_user_profile(
    current_user_id: Annotated[str, Depends(get_current_user_id)],
    db: Session = Depends(get_db)
):
    """
    Get current authenticated user's profile.
    
    Returns profile data for the authenticated user.
    """
    user_id = UUID(current_user_id)
    
    profile = db.query(Profile).filter(Profile.id == user_id).first()
    
    if not profile:
        # Auto-create profile if it doesn't exist
        # This handles cases where user was created in Supabase Auth
        # but profile wasn't created yet
        profile = Profile(id=user_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    
    return profile


@router.patch("/me", response_model=ProfileResponse)
async def update_current_user_profile(
    profile_update: ProfileUpdate,
    current_user_id: Annotated[str, Depends(get_current_user_id)],
    db: Session = Depends(get_db)
):
    """
    Update current authenticated user's profile.
    
    Users can only update their own profile.
    """
    user_id = UUID(current_user_id)
    
    profile = db.query(Profile).filter(Profile.id == user_id).first()
    
    if not profile:
        # Auto-create profile if it doesn't exist
        profile = Profile(id=user_id)
        db.add(profile)
    
    # Update fields
    update_data = profile_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)
    
    db.commit()
    db.refresh(profile)
    
    return profile


@router.get("/me/auth", response_model=dict)
async def get_current_user_from_supabase(
    current_user: Annotated[dict, Depends(get_current_user)]
):
    """
    Get current authenticated user's details from JWT token.
    
    Returns user data decoded from the JWT token (fast, no external API calls).
    """
    # JWT token already contains all the user data we need
    # No need to make external API call to Supabase
    return {
        "id": current_user.get("sub"),
        "email": current_user.get("email"),
        "phone": current_user.get("phone"),
        "email_confirmed_at": current_user.get("email_confirmed_at"),
        "phone_confirmed_at": current_user.get("phone_confirmed_at"),
        "role": current_user.get("role"),
        "app_metadata": current_user.get("app_metadata", {}),
        "user_metadata": current_user.get("user_metadata", {}),
        # Additional token claims
        "aud": current_user.get("aud"),
        "iat": current_user.get("iat"),
        "exp": current_user.get("exp")
    }
