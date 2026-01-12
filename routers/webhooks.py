"""
Webhook endpoints for billing provider integrations.
Handles events from Lemon Squeezy and other billing providers.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from uuid import UUID
import json

from database import get_db
from models import BillingEvent, Subscription, SubscriptionHistory
from schemas import MessageResponse
from config import get_settings
from utils.security import verify_webhook_signature

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])
settings = get_settings()


@router.post("/lemon-squeezy", response_model=MessageResponse)
async def lemon_squeezy_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_signature: Optional[str] = Header(None)
):
    """
    Handle webhooks from Lemon Squeezy.
    
    Processes billing events such as:
    - subscription_created
    - subscription_updated
    - subscription_cancelled
    - subscription_resumed
    - subscription_expired
    - subscription_payment_success
    - subscription_payment_failed
    
    More info: https://docs.lemonsqueezy.com/api/webhooks
    """
    # Get raw body for signature verification
    body = await request.body()
    body_str = body.decode()
    
    # Verify webhook signature if configured
    if settings.LEMON_SQUEEZY_WEBHOOK_SECRET and x_signature:
        is_valid = verify_webhook_signature(
            body_str,
            x_signature,
            settings.LEMON_SQUEEZY_WEBHOOK_SECRET
        )
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature"
            )
    
    # Parse webhook payload
    try:
        payload = json.loads(body_str)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )
    
    # Extract event type
    event_type = payload.get("meta", {}).get("event_name")
    if not event_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing event_name in payload"
        )
    
    # Extract subscription data
    data = payload.get("data", {})
    attributes = data.get("attributes", {})
    
    # Get user ID from custom data or metadata
    custom_data = attributes.get("custom_data", {})
    user_id_str = custom_data.get("user_id")
    
    user_id = None
    if user_id_str:
        try:
            user_id = UUID(user_id_str)
        except ValueError:
            pass
    
    # Create billing event record
    billing_event = BillingEvent(
        user_id=user_id,
        event_type=event_type,
        payload=payload,
        processed=False
    )
    db.add(billing_event)
    db.commit()
    
    # Process event
    try:
        await process_lemon_squeezy_event(event_type, payload, db)
        billing_event.processed = True
        db.commit()
    except Exception as e:
        billing_event.error_message = str(e)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing webhook: {str(e)}"
        )
    
    return MessageResponse(
        message="Webhook processed successfully",
        detail=f"Event type: {event_type}"
    )


async def process_lemon_squeezy_event(
    event_type: str,
    payload: Dict[str, Any],
    db: Session
):
    """
    Process different types of Lemon Squeezy events.
    
    Updates subscription status and creates history entries.
    """
    data = payload.get("data", {})
    attributes = data.get("attributes", {})
    
    # Get subscription ID from Lemon Squeezy
    ls_subscription_id = str(data.get("id"))
    
    # Find subscription in database
    subscription = db.query(Subscription).filter(
        Subscription.lemon_squeezy_subscription_id == ls_subscription_id
    ).first()
    
    if not subscription:
        # For subscription_created, we might need to create it
        if event_type == "subscription_created":
            custom_data = attributes.get("custom_data", {})
            user_id_str = custom_data.get("user_id")
            plan_id_str = custom_data.get("plan_id")
            
            if not user_id_str or not plan_id_str:
                raise ValueError("Missing user_id or plan_id in custom_data")
            
            subscription = Subscription(
                user_id=UUID(user_id_str),
                plan_id=UUID(plan_id_str),
                lemon_squeezy_subscription_id=ls_subscription_id,
                status="active"
            )
            db.add(subscription)
            db.commit()
            db.refresh(subscription)
            
            # Create history entry
            history = SubscriptionHistory(
                subscription_id=subscription.id,
                event="created",
                event_metadata={"source": "lemon_squeezy"}
            )
            db.add(history)
            db.commit()
        else:
            # Subscription not found and not a creation event
            raise ValueError(f"Subscription not found: {ls_subscription_id}")
    
    # Update subscription based on event type
    if event_type == "subscription_updated":
        status_value = attributes.get("status")
        if status_value:
            subscription.status = status_value
            
            history = SubscriptionHistory(
                subscription_id=subscription.id,
                event="updated",
                event_metadata={"new_status": status_value}
            )
            db.add(history)
    
    elif event_type == "subscription_cancelled":
        subscription.status = "canceled"
        subscription.canceled_at = attributes.get("ends_at")
        
        history = SubscriptionHistory(
            subscription_id=subscription.id,
            event="canceled",
            event_metadata={"source": "lemon_squeezy"}
        )
        db.add(history)
    
    elif event_type == "subscription_resumed":
        subscription.status = "active"
        subscription.canceled_at = None
        
        history = SubscriptionHistory(
            subscription_id=subscription.id,
            event="resumed",
            event_metadata={"source": "lemon_squeezy"}
        )
        db.add(history)
    
    elif event_type == "subscription_expired":
        subscription.status = "expired"
        
        history = SubscriptionHistory(
            subscription_id=subscription.id,
            event="expired",
            event_metadata={"source": "lemon_squeezy"}
        )
        db.add(history)
    
    elif event_type == "subscription_payment_success":
        # Record successful payment
        history = SubscriptionHistory(
            subscription_id=subscription.id,
            event="payment_success",
            amount=attributes.get("total"),
            event_metadata={"source": "lemon_squeezy"}
        )
        db.add(history)
    
    elif event_type == "subscription_payment_failed":
        # Record failed payment
        history = SubscriptionHistory(
            subscription_id=subscription.id,
            event="payment_failed",
            event_metadata={"source": "lemon_squeezy"}
        )
        db.add(history)
    
    db.commit()
