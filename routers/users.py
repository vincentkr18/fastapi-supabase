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
from utils.auth import get_current_user_id
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
    current_user_id: Annotated[str, Depends(get_current_user_id)]
):
    """
    Get current authenticated user's details directly from Supabase Auth.
    
    Returns complete user data from Supabase authentication system.
    """
    try:
        supabase = get_supabase_client()
        
        # Query user from Supabase Auth
        response = supabase.auth.admin.get_user_by_id(current_user_id)
        
        if not response or not response.user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found in Supabase Auth"
            )
        
        user = response.user
        
        # Return user details
        return {
            "id": user.id,
            "email": user.email,
            "phone": user.phone,
            "email_confirmed_at": user.email_confirmed_at,
            "phone_confirmed_at": user.phone_confirmed_at,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "last_sign_in_at": user.last_sign_in_at,
            "role": user.role,
            "app_metadata": user.app_metadata,
            "user_metadata": user.user_metadata,
            "identities": [
                {
                    "provider": getattr(identity, "provider", None),
                    "id": getattr(identity, "id", None),
                    "identity_id": getattr(identity, "identity_id", None),
                    "user_id": getattr(identity, "user_id", None),
                    "created_at": getattr(identity, "created_at", None),
                    "updated_at": getattr(identity, "updated_at", None),
                    "last_sign_in_at": getattr(identity, "last_sign_in_at", None)
                }
                for identity in (user.identities or [])
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user from Supabase: {str(e)}"
        )
