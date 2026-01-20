# schemas.py - Pydantic schemas for Dodo Payments

from pydantic import BaseModel, EmailStr, Field, UUID4
from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal
from uuid import UUID


# Enums
class PaymentProvider(str):
    DODO = "dodo"
    APPLE = "apple"
    GOOGLE = "google"


class PaymentStatus(str):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class SubscriptionStatus(str):
    ACTIVE = "active"
    CANCELED = "canceled"
    EXPIRED = "expired"
    PAST_DUE = "past_due"
    TRIAL = "trial"


# Plan Schemas
class PlanBase(BaseModel):
    name: str
    description: Optional[str] = None
    pricing: Dict[str, Any]  # {"monthly_usd": 9.99, "annual_usd": 99}
    features: Dict[str, Any] = {}
    provider_ids: Dict[str, str] = {}


class PlanCreate(PlanBase):
    pass


class PlanUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    pricing: Optional[Dict[str, Any]] = None
    features: Optional[Dict[str, Any]] = None
    provider_ids: Optional[Dict[str, str]] = None
    is_active: Optional[bool] = None


class PlanResponse(PlanBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# Subscription Schemas
class SubscriptionBase(BaseModel):
    plan_id: UUID
    provider: str
    provider_subscription_id: str


class SubscriptionCreate(SubscriptionBase):
    current_period_start: datetime
    current_period_end: datetime
    trial_end: Optional[datetime] = None


class SubscriptionUpdate(BaseModel):
    status: Optional[str] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: Optional[bool] = None


class SubscriptionResponse(SubscriptionBase):
    id: UUID
    user_id: UUID
    status: str
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool
    canceled_at: Optional[datetime]
    trial_end: Optional[datetime]
    event_log: List[Dict[str, Any]] = []
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# Payment Schemas
class PaymentCreate(BaseModel):
    subscription_id: Optional[UUID] = None
    provider: str
    provider_payment_id: str
    amount: Decimal
    currency: str = "USD"
    metadata: Dict[str, Any] = {}


class PaymentResponse(BaseModel):
    id: UUID
    user_id: UUID
    subscription_id: Optional[UUID]
    provider: str
    provider_payment_id: str
    amount: Decimal
    currency: str
    status: str
    refund_amount: Optional[Decimal]
    refund_reason: Optional[str]
    refunded_at: Optional[datetime]
    metadata: Dict[str, Any]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


# Dodo Payment Schemas
class DodoPaymentRequest(BaseModel):
    plan_id: UUID
    payment_method: str = "card"
    return_url: Optional[str] = None
    metadata: Dict[str, Any] = {}


class DodoPaymentResponse(BaseModel):
    payment_id: str
    checkout_url: str
    amount: Decimal
    currency: str
    status: str


# Apple IAP Schemas
class AppleReceiptValidation(BaseModel):
    receipt_data: str
    exclude_old_transactions: bool = False


class AppleVerifyResponse(BaseModel):
    status: int
    receipt: Dict[str, Any]
    latest_receipt_info: Optional[List[Dict[str, Any]]] = None
    pending_renewal_info: Optional[List[Dict[str, Any]]] = None


# Google Play Schemas
class GooglePurchaseToken(BaseModel):
    purchase_token: str
    product_id: str
    subscription: bool = True


class GoogleVerifyResponse(BaseModel):
    kind: str
    start_time_millis: str
    expiry_time_millis: str
    auto_renewing: bool
    price_currency_code: str
    price_amount_micros: str
    payment_state: int


# Webhook Schemas
class WebhookEventResponse(BaseModel):
    id: UUID
    provider: str
    provider_event_id: Optional[str]
    event_type: str
    processed: bool
    received_at: datetime
    processed_at: Optional[datetime]
    error_message: Optional[str]

    class Config:
        from_attributes = True


# Cancel Subscription Schema
class CancelSubscriptionRequest(BaseModel):
    cancel_at_period_end: bool = True
    reason: Optional[str] = None


# Refund Schema
class RefundRequest(BaseModel):
    payment_id: UUID
    amount: Optional[Decimal] = None  # None = full refund
    reason: Optional[str] = None