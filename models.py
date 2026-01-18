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

class Profile(Base):
    """
    User profile table - supplements Supabase auth.users.
    Uses same UUID as auth.users.id.
    """
    __tablename__ = "profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    display_name = Column(String(150), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    extra_meta = Column(JSON, nullable=True, default={})
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    subscriptions = relationship("Subscription", back_populates="user")
    api_keys = relationship("APIKey", back_populates="user")
    billing_events = relationship("BillingEvent", back_populates="user")


class Plan(Base):
    """
    SaaS pricing plans.
    """
    __tablename__ = "plans"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    lemon_squeezy_product_id = Column(String(255), nullable=True)
    price_monthly = Column(Numeric(10, 2), nullable=True)
    price_annually = Column(Numeric(10, 2), nullable=True)
    features = Column(JSON, nullable=True, default={})
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    subscriptions = relationship("Subscription", back_populates="plan")


class Subscription(Base):
    """
    User subscriptions to plans.
    """
    __tablename__ = "subscriptions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False, index=True)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("plans.id"), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="active")  # active, canceled, expired, past_due
    start_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    end_date = Column(DateTime, nullable=True)
    lemon_squeezy_subscription_id = Column(String(255), nullable=True, unique=True, index=True)
    price_id = Column(String(255), nullable=True)
    auto_renew = Column(Boolean, default=True, nullable=False)
    canceled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("Profile", back_populates="subscriptions")
    plan = relationship("Plan", back_populates="subscriptions")
    history = relationship("SubscriptionHistory", back_populates="subscription")


class SubscriptionHistory(Base):
    """
    Audit log for subscription changes.
    """
    __tablename__ = "subscription_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey("subscriptions.id"), nullable=False, index=True)
    event = Column(String(100), nullable=False)  # created, renewed, canceled, upgraded, downgraded
    amount = Column(Numeric(10, 2), nullable=True)
    event_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    event_metadata = Column(JSON, nullable=True, default={})
    
    # Relationships
    subscription = relationship("Subscription", back_populates="history")


class APIKey(Base):
    """
    API keys for users with API-enabled plans.
    """
    __tablename__ = "api_keys"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False, index=True)
    key_hash = Column(String(255), nullable=False, unique=True, index=True)  # Hashed key
    key_prefix = Column(String(20), nullable=False)  # First few chars for display
    name = Column(String(100), nullable=True)  # User-defined key name
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    revoked = Column(Boolean, default=False, nullable=False)
    last_used = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("Profile", back_populates="api_keys")


class BillingEvent(Base):
    """
    Webhook events from billing provider (Lemon Squeezy).
    """
    __tablename__ = "billing_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    payload = Column(JSON, nullable=False)
    received_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed = Column(Boolean, default=False, nullable=False)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("Profile", back_populates="billing_events")



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
    user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False, index=True)
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
    user = relationship("Profile")
