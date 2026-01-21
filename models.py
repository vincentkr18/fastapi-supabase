"""
SQLAlchemy database models.
All models reference auth.users.id from Supabase Auth.
"""
from sqlalchemy import (
    Column, String, Boolean, DateTime, Numeric, Text,
    ForeignKey, UUID, JSON, TIMESTAMP, text
)
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
from waitlist_model import Waitlist
import uuid
# models.py
from sqlalchemy import Column, Integer, String, Table, ForeignKey



class Plan(Base):
    """
    Pricing plans - supports multiple providers and pricing models.
    """
    __tablename__ = "plans"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Pricing - store all variants in JSON
    # e.g., {"monthly_usd": 9.99, "annual_usd": 99, "monthly_inr": 799}
    pricing = Column(JSON, nullable=False, default=dict)
    
    # Features available in this plan
    features = Column(JSON, nullable=True, default=dict)
    
    # Provider-specific IDs stored in JSON
    # e.g., {"dodo": "prod_123", "apple": "com.app.premium", "google": "premium_monthly"}
    provider_ids = Column(JSON, nullable=True, default=dict)
    
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    subscriptions = relationship("Subscription", back_populates="plan")


class Subscription(Base):
    """
    User subscriptions - consolidated for all providers.
    """
    __tablename__ = "subscriptions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # Directly reference Supabase auth.users.id
    plan_id = Column(UUID(as_uuid=True), ForeignKey("plans.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    # Provider info
    # Values: "dodo", "apple", "google"
    provider = Column(String(20), nullable=False, index=True)
    provider_subscription_id = Column(String(255), unique=True, index=True, nullable=False)
    
    # Status
    # Values: "active", "canceled", "expired", "past_due", "trial"
    status = Column(String(50), nullable=False, default="active", index=True)
    
    # Dates
    current_period_start = Column(DateTime, nullable=False)
    current_period_end = Column(DateTime, nullable=False)
    cancel_at_period_end = Column(Boolean, default=False, nullable=False)
    canceled_at = Column(DateTime, nullable=True)
    trial_end = Column(DateTime, nullable=True)
    
    # Store event history as JSON instead of separate table
    # e.g., [{"event": "created", "date": "2024-01-01T00:00:00", "metadata": {}}]
    event_log = Column(JSON, nullable=True, default=list)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    # user = relationship("Profile", back_populates="subscriptions")
    plan = relationship("Plan", back_populates="subscriptions")
    payments = relationship("Payment", back_populates="subscription", cascade="all, delete-orphan")


class Payment(Base):
    """
    Payment transactions - supports multiple payment providers.
    """
    __tablename__ = "payments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # Directly reference Supabase auth.users.id
    subscription_id = Column(UUID(as_uuid=True), ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Provider
    # Values: "dodo", "apple", "google"
    provider = Column(String(20), nullable=False, index=True)
    provider_payment_id = Column(String(255), unique=True, index=True, nullable=False)
    
    # Amount
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    
    # Status
    # Values: "pending", "completed", "failed", "refunded", "partially_refunded"
    status = Column(String(50), nullable=False, default="pending", index=True)
    
    # Refund info (instead of separate table)
    refund_amount = Column(Numeric(10, 2), nullable=True)
    refund_reason = Column(Text, nullable=True)
    refunded_at = Column(DateTime, nullable=True)
    
    # Extra metadata - store everything else here
    # payment_method, description, proration_details, provider-specific data, etc.
    extra_metadata = Column(JSON, nullable=True, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    # user = relationship("Profile", back_populates="payments")
    subscription = relationship("Subscription", back_populates="payments")


class APIKey(Base):
    """
    API keys for users with API-enabled plans.
    Optional - only needed if you're offering API access.
    """
    __tablename__ = "api_keys"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # Directly reference Supabase auth.users.id
    
    # Security
    key_hash = Column(String(255), nullable=False, unique=True, index=True)  # Hashed key
    key_prefix = Column(String(20), nullable=False)  # First few chars for display (e.g., "sk_test_abc...")
    
    # Metadata
    name = Column(String(100), nullable=True)  # User-defined key name
    
    # Status
    revoked = Column(Boolean, default=False, nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    last_used = Column(DateTime, nullable=True)
    
    # Relationships
    # user = relationship("Profile", backref="api_keys")


class WebhookEvent(Base):
    """
    Webhook events - provider agnostic.
    Stores all webhook events from all providers for debugging and audit.
    """
    __tablename__ = "webhook_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Provider info
    # Values: "dodo", "apple", "google"
    provider = Column(String(20), nullable=False, index=True)
    provider_event_id = Column(String(255), unique=True, index=True, nullable=True)
    event_type = Column(String(100), nullable=False, index=True)
    
    # Event data
    payload = Column(JSON, nullable=False)
    signature = Column(String(500), nullable=True)  # For verification
    
    # Processing status
    processed = Column(Boolean, default=False, nullable=False, index=True)
    processed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    received_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)



video_tags = Table(
    "video_tags",
    Base.metadata,
    Column("video_id", ForeignKey("videos.id"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True),
)

class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    video_url = Column(String, nullable=False)
    thumbnail_url = Column(String, nullable=False)
    preview_url = Column(String, nullable=False)

    tags = relationship("Tag", secondary=video_tags, back_populates="videos")


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)

    videos = relationship("Video", secondary=video_tags, back_populates="tags")




class GenerationJob(Base):
    __tablename__ = "generation_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(36), unique=True, nullable=False, index=True)
    model_type = Column(String(50), nullable=False)  # lip_sync, sora_2, kling, veo_3
    status = Column(String(20), nullable=False, default="pending")  # pending, processing, completed, failed
    progress = Column(Integer, default=0)
    
    # Input parameters
    aspect_ratio = Column(String(10), nullable=False)
    prompt = Column(Text, nullable=True)
    video_template_id = Column(Integer, ForeignKey('videos.id'), nullable=True)
    
    # File paths
    audio_file_path = Column(String, nullable=True)
    product_image_path = Column(String, nullable=True)
    output_video_path = Column(String, nullable=True)
    
    # Text-to-speech parameters
    text_input = Column(Text, nullable=True)
    voice_id = Column(String(100), nullable=True)  # ElevenLabs voice ID
    
    # Additional metadata
    character_description = Column(Text, nullable=True)
    environment_description = Column(Text, nullable=True)
    gestures = Column(Text, nullable=True)
    dialogue = Column(Text, nullable=True)
    voice_tone = Column(String(100), nullable=True)
    
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    video_template = relationship("Video", foreign_keys=[video_template_id])
    #user = relationship("Profile", back_populates="generation_jobs")


class UserMedia(Base):
    """
    User uploaded media files (audio and pictures) stored in S3.
    """
    __tablename__ = "user_media"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # Directly reference Supabase auth.users.id
    media_type = Column(String(20), nullable=False)  # audio, image
    file_name = Column(String(255), nullable=False)
    original_file_name = Column(String(255), nullable=False)
    s3_key = Column(String(500), nullable=False)  # S3 object key
    s3_url = Column(String(1000), nullable=False)  # Full S3 URL
    file_size = Column(Integer, nullable=True)  # Size in bytes
    mime_type = Column(String(100), nullable=True)  # e.g., audio/mpeg, image/jpeg
    media_metadata = Column(JSON, nullable=True, default={})  # Additional metadata (duration, dimensions, etc.)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    # user = relationship("Profile")
