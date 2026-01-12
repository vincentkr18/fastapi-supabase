"""
Subscription management endpoints.
Authenticated users can manage their own subscriptions.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated, List, Optional
from uuid import UUID
from datetime import datetime

from database import get_db
from models import Subscription, SubscriptionHistory, Plan, Profile
from schemas import (
    SubscriptionCreate,
    SubscriptionResponse,
    SubscriptionCancel,
    SubscriptionHistoryResponse,
    MessageResponse
)
from utils.auth import get_current_user_id

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


@router.post("", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    subscription_data: SubscriptionCreate,
    current_user_id: Annotated[str, Depends(get_current_user_id)],
    db: Session = Depends(get_db)
):
    """
    Create a new subscription for the current user.
    
    This endpoint is typically called after successful payment processing
    via Lemon Squeezy or another billing provider.
    """
    user_id = UUID(current_user_id)
    
    # Verify plan exists
    plan = db.query(Plan).filter(Plan.id == subscription_data.plan_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found"
        )
    
    if not plan.active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This plan is not currently available"
        )
    
    # Check for existing active subscription
    existing_sub = db.query(Subscription).filter(
        Subscription.user_id == user_id,
        Subscription.status == "active"
    ).first()
    
    if existing_sub:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has an active subscription"
        )
    
    # Create subscription
    subscription = Subscription(
        user_id=user_id,
        plan_id=subscription_data.plan_id,
        status="active",
        lemon_squeezy_subscription_id=subscription_data.lemon_squeezy_subscription_id,
        price_id=subscription_data.price_id
    )
    
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    
    # Create history entry
    history = SubscriptionHistory(
        subscription_id=subscription.id,
        event="created",
        amount=plan.price_monthly,
        event_metadata={
            "plan_name": plan.name,
            "plan_id": str(plan.id)
        }
    )
    db.add(history)
    db.commit()
    
    # Load plan relationship
    db.refresh(subscription)
    
    return subscription


@router.get("/me", response_model=Optional[SubscriptionResponse])
async def get_current_subscription(
    current_user_id: Annotated[str, Depends(get_current_user_id)],
    db: Session = Depends(get_db)
):
    """
    Get current user's active subscription.
    
    Returns the active subscription or null if no active subscription exists.
    """
    user_id = UUID(current_user_id)
    
    subscription = db.query(Subscription).filter(
        Subscription.user_id == user_id,
        Subscription.status == "active"
    ).first()
    
    return subscription


@router.post("/me/cancel", response_model=MessageResponse)
async def cancel_subscription(
    cancel_data: SubscriptionCancel,
    current_user_id: Annotated[str, Depends(get_current_user_id)],
    db: Session = Depends(get_db)
):
    """
    Cancel current user's active subscription.
    
    The subscription will remain active until the end of the billing period.
    """
    user_id = UUID(current_user_id)
    
    subscription = db.query(Subscription).filter(
        Subscription.user_id == user_id,
        Subscription.status == "active"
    ).first()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )
    
    # Update subscription
    subscription.status = "canceled"
    subscription.canceled_at = datetime.utcnow()
    subscription.auto_renew = False
    
    # Create history entry
    history = SubscriptionHistory(
        subscription_id=subscription.id,
        event="canceled",
        event_metadata={
            "reason": cancel_data.reason,
            "canceled_by": "user"
        }
    )
    
    db.add(history)
    db.commit()
    
    return MessageResponse(
        message="Subscription canceled successfully",
        detail="Your subscription will remain active until the end of the billing period"
    )


@router.get("/me/history", response_model=List[SubscriptionHistoryResponse])
async def get_subscription_history(
    current_user_id: Annotated[str, Depends(get_current_user_id)],
    db: Session = Depends(get_db)
):
    """
    Get subscription history for the current user.
    
    Returns all subscription events for all user's subscriptions.
    """
    user_id = UUID(current_user_id)
    
    # Get all user's subscriptions
    subscription_ids = db.query(Subscription.id).filter(
        Subscription.user_id == user_id
    ).all()
    
    subscription_ids = [sub_id for (sub_id,) in subscription_ids]
    
    # Get history for all subscriptions
    history = db.query(SubscriptionHistory).filter(
        SubscriptionHistory.subscription_id.in_(subscription_ids)
    ).order_by(SubscriptionHistory.event_date.desc()).all()
    
    return history
