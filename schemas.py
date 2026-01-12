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
