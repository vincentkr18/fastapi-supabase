"""
Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
from decimal import Decimal


# ============ Profile Schemas ============

class ProfileBase(BaseModel):
    """Base profile schema."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    extra_meta: Optional[Dict[str, Any]] = {}


class ProfileUpdate(ProfileBase):
    """Schema for updating profile."""
    pass


class ProfileResponse(ProfileBase):
    """Schema for profile response."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============ Plan Schemas ============

class PlanBase(BaseModel):
    """Base plan schema."""
    name: str
    description: Optional[str] = None
    price_monthly: Optional[Decimal] = None
    price_annually: Optional[Decimal] = None
    features: Optional[Dict[str, Any]] = {}


class PlanCreate(PlanBase):
    """Schema for creating plan."""
    lemon_squeezy_product_id: Optional[str] = None
    active: bool = True


class PlanResponse(PlanBase):
    """Schema for plan response."""
    id: UUID
    lemon_squeezy_product_id: Optional[str] = None
    active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============ Subscription Schemas ============

class SubscriptionCreate(BaseModel):
    """Schema for creating subscription."""
    plan_id: UUID
    lemon_squeezy_subscription_id: Optional[str] = None
    price_id: Optional[str] = None


class SubscriptionUpdate(BaseModel):
    """Schema for updating subscription."""
    status: Optional[str] = None
    end_date: Optional[datetime] = None
    auto_renew: Optional[bool] = None


class SubscriptionResponse(BaseModel):
    """Schema for subscription response."""
    id: UUID
    user_id: UUID
    plan_id: UUID
    status: str
    start_date: datetime
    end_date: Optional[datetime] = None
    lemon_squeezy_subscription_id: Optional[str] = None
    price_id: Optional[str] = None
    auto_renew: bool
    canceled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    # Nested plan info
    plan: Optional[PlanResponse] = None
    
    model_config = ConfigDict(from_attributes=True)


class SubscriptionCancel(BaseModel):
    """Schema for canceling subscription."""
    reason: Optional[str] = None


# ============ Subscription History Schemas ============

class SubscriptionHistoryResponse(BaseModel):
    """Schema for subscription history response."""
    id: UUID
    subscription_id: UUID
    event: str
    amount: Optional[Decimal] = None
    event_date: datetime
    event_metadata: Optional[Dict[str, Any]] = {}
    
    model_config = ConfigDict(from_attributes=True)


# ============ API Key Schemas ============

class APIKeyCreate(BaseModel):
    """Schema for creating API key."""
    name: Optional[str] = Field(None, max_length=100, description="Optional name for the API key")
    expires_at: Optional[datetime] = Field(None, description="Optional expiration date")


class APIKeyResponse(BaseModel):
    """Schema for API key response."""
    id: UUID
    key_prefix: str
    name: Optional[str] = None
    created_at: datetime
    expires_at: Optional[datetime] = None
    revoked: bool
    last_used: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class APIKeyCreateResponse(APIKeyResponse):
    """Schema for API key creation response (includes full key once)."""
    key: str  # Full key only shown on creation


# ============ Billing Event Schemas ============

class BillingEventCreate(BaseModel):
    """Schema for creating billing event."""
    event_type: str
    payload: Dict[str, Any]


class BillingEventResponse(BaseModel):
    """Schema for billing event response."""
    id: UUID
    user_id: Optional[UUID] = None
    event_type: str
    payload: Dict[str, Any]
    received_at: datetime
    processed: bool
    error_message: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


# ============ Common Response Schemas ============

class MessageResponse(BaseModel):
    """Generic message response."""
    message: str
    detail: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str
    detail: Optional[str] = None
    status_code: int

# schemas.py

from pydantic import BaseModel
from typing import List

class TagOut(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)

class VideoOut(BaseModel):
    id: int
    title: str
    video_url: str
    thumbnail_url: str
    preview_url: str
    tags: List[TagOut]

    model_config = ConfigDict(from_attributes=True)
    
    @classmethod
    def model_validate(cls, obj, **kwargs):
        """Override to update URL transformations to 1080x1920"""
        instance = super().model_validate(obj, **kwargs)
        
        # Update thumbnail URL transformations
        if instance.thumbnail_url:
            instance.thumbnail_url = instance.thumbnail_url.replace(
                'w_400,h_250,c_fill', 'w_1080,h_1920,c_fill'
            )
        
        # Update preview URL transformations
        if instance.preview_url:
            # Replace old transformation or add new one
            if 'so_0,du_4/' in instance.preview_url:
                instance.preview_url = instance.preview_url.replace(
                    'so_0,du_4/', 'so_0,du_4,w_1080,h_1920,c_fill/'
                )
        
        return instance


from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class AspectRatio(str, Enum):
    SQUARE = "1:1"
    PORTRAIT = "9:16"
    LANDSCAPE = "16:9"
    WIDESCREEN = "21:9"


class VideoModel(str, Enum):
    LIP_SYNC = "lip_sync"
    SORA_2 = "sora_2"
    KLING = "kling"
    VEO_3 = "veo_3"


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobResponse(BaseModel):
    job_id: str
    status: str
    model: str
    progress: int
    created_at: datetime
    message: str = "Job submitted successfully"
    video_generated_path: Optional[str] = None

    class Config:
        from_attributes = True


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: int
    video_url: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True