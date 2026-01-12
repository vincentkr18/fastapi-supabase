"""
API key management endpoints.
Authenticated users can create, list, and revoke their own API keys.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated, List
from uuid import UUID
from datetime import datetime

from database import get_db
from models import APIKey
from schemas import APIKeyCreate, APIKeyResponse, APIKeyCreateResponse, MessageResponse
from utils.auth import get_current_user_id
from utils.security import generate_api_key, hash_api_key, get_api_key_prefix

router = APIRouter(prefix="/api-keys", tags=["API Keys"])


@router.post("", response_model=APIKeyCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user_id: Annotated[str, Depends(get_current_user_id)],
    db: Session = Depends(get_db)
):
    """
    Generate a new API key for the current user.
    
    The full API key is only shown once upon creation.
    Store it securely - it cannot be retrieved later.
    """
    user_id = UUID(current_user_id)
    
    # Generate new API key
    api_key = generate_api_key()
    key_hash = hash_api_key(api_key)
    key_prefix = get_api_key_prefix(api_key, length=12)
    
    # Create API key record
    db_key = APIKey(
        user_id=user_id,
        key_hash=key_hash,
        key_prefix=key_prefix,
        name=key_data.name,
        expires_at=key_data.expires_at
    )
    
    db.add(db_key)
    db.commit()
    db.refresh(db_key)
    
    # Return response with full key (only time it's shown)
    response = APIKeyCreateResponse(
        id=db_key.id,
        key=api_key,  # Full key only on creation
        key_prefix=db_key.key_prefix,
        name=db_key.name,
        created_at=db_key.created_at,
        expires_at=db_key.expires_at,
        revoked=db_key.revoked,
        last_used=db_key.last_used
    )
    
    return response


@router.get("", response_model=List[APIKeyResponse])
async def list_api_keys(
    current_user_id: Annotated[str, Depends(get_current_user_id)],
    db: Session = Depends(get_db),
    include_revoked: bool = False
):
    """
    List all API keys for the current user.
    
    By default, only returns active (non-revoked) keys.
    """
    user_id = UUID(current_user_id)
    
    query = db.query(APIKey).filter(APIKey.user_id == user_id)
    
    if not include_revoked:
        query = query.filter(APIKey.revoked == False)
    
    keys = query.order_by(APIKey.created_at.desc()).all()
    
    return keys


@router.delete("/{key_id}", response_model=MessageResponse)
async def revoke_api_key(
    key_id: UUID,
    current_user_id: Annotated[str, Depends(get_current_user_id)],
    db: Session = Depends(get_db)
):
    """
    Revoke an API key.
    
    Users can only revoke their own keys.
    Revoked keys cannot be used for authentication.
    """
    user_id = UUID(current_user_id)
    
    api_key = db.query(APIKey).filter(
        APIKey.id == key_id,
        APIKey.user_id == user_id
    ).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    if api_key.revoked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="API key is already revoked"
        )
    
    # Revoke the key
    api_key.revoked = True
    db.commit()
    
    return MessageResponse(
        message="API key revoked successfully",
        detail=f"Key {api_key.key_prefix} has been revoked"
    )
