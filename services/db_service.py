from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional, List
from datetime import datetime
from uuid import UUID
import logging

# Import your models here
# from models import Profile, Plan, Subscription, Payment, WebhookEvent
# For now using generic imports
from models import *

logger = logging.getLogger(__name__)


class PaymentDatabaseService:
    """Service for database operations related to payments"""
    
    @staticmethod
    def create_subscription(
        db: Session,
        user_id: UUID,
        plan_id: UUID,
        provider: str,
        provider_subscription_id: str,
        current_period_start: datetime,
        current_period_end: datetime,
        trial_end: Optional[datetime] = None
    ) -> Subscription:
        """Create a new subscription"""
        subscription = Subscription(
            user_id=user_id,
            plan_id=plan_id,
            provider=provider,
            provider_subscription_id=provider_subscription_id,
            status="active",
            current_period_start=current_period_start,
            current_period_end=current_period_end,
            trial_end=trial_end,
            event_log=[{
                "event": "created",
                "date": datetime.utcnow().isoformat(),
                "metadata": {"provider": provider}
            }]
        )
        
        db.add(subscription)
        db.commit()
        db.refresh(subscription)
        
        return subscription
    
    @staticmethod
    def get_subscription(db: Session, subscription_id: UUID) -> Optional[Subscription]:
        """Get subscription by ID"""
        return db.query(Subscription).filter(Subscription.id == subscription_id).first()
    
    @staticmethod
    def get_subscription_by_provider_id(db: Session, provider_subscription_id: str) -> Optional[Subscription]:
        """Get subscription by provider subscription ID"""
        return db.query(Subscription).filter(
            Subscription.provider_subscription_id == provider_subscription_id
        ).first()
    
    @staticmethod
    def get_user_subscriptions(
        db: Session,
        user_id: UUID,
        active_only: bool = False
    ) -> List[Subscription]:
        """Get all subscriptions for a user"""
        query = db.query(Subscription).filter(Subscription.user_id == user_id)
        
        if active_only:
            query = query.filter(Subscription.status == "active")
        
        return query.all()
    
    @staticmethod
    def update_subscription_status(
        db: Session,
        subscription_id: UUID,
        status: str,
        event: str,
        metadata: dict = None
    ) -> Subscription:
        """Update subscription status and log event"""
        subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
        
        if not subscription:
            raise ValueError(f"Subscription {subscription_id} not found")
        
        subscription.status = status
        
        # Add event to log
        event_log = subscription.event_log or []
        event_log.append({
            "event": event,
            "date": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        })
        subscription.event_log = event_log
        
        db.commit()
        db.refresh(subscription)
        
        return subscription
    
    @staticmethod
    def cancel_subscription(
        db: Session,
        subscription_id: UUID,
        cancel_at_period_end: bool = True,
        reason: Optional[str] = None
    ) -> Subscription:
        """Cancel a subscription"""
        subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
        
        if not subscription:
            raise ValueError(f"Subscription {subscription_id} not found")
        
        subscription.cancel_at_period_end = cancel_at_period_end
        subscription.canceled_at = datetime.utcnow()
        
        if not cancel_at_period_end:
            subscription.status = "canceled"
        
        # Add event to log
        event_log = subscription.event_log or []
        event_log.append({
            "event": "canceled",
            "date": datetime.utcnow().isoformat(),
            "metadata": {
                "cancel_at_period_end": cancel_at_period_end,
                "reason": reason
            }
        })
        subscription.event_log = event_log
        
        db.commit()
        db.refresh(subscription)
        
        return subscription
    
    @staticmethod
    def create_payment(
        db: Session,
        user_id: UUID,
        provider: str,
        provider_payment_id: str,
        amount: float,
        currency: str = "USD",
        subscription_id: Optional[UUID] = None,
        metadata: dict = None
    ) -> Payment:
        """Create a payment record"""
        payment = Payment(
            user_id=user_id,
            subscription_id=subscription_id,
            provider=provider,
            provider_payment_id=provider_payment_id,
            amount=amount,
            currency=currency,
            status="pending",
            metadata=metadata or {}
        )
        
        db.add(payment)
        db.commit()
        db.refresh(payment)
        
        return payment
    
    @staticmethod
    def update_payment_status(
        db: Session,
        payment_id: UUID,
        status: str,
        completed_at: Optional[datetime] = None
    ) -> Payment:
        """Update payment status"""
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        
        if not payment:
            raise ValueError(f"Payment {payment_id} not found")
        
        payment.status = status
        
        if status == "completed" and completed_at:
            payment.completed_at = completed_at
        
        db.commit()
        db.refresh(payment)
        
        return payment
    
    @staticmethod
    def get_payment_by_provider_id(db: Session, provider_payment_id: str) -> Optional[Payment]:
        """Get payment by provider payment ID"""
        return db.query(Payment).filter(
            Payment.provider_payment_id == provider_payment_id
        ).first()
    
    @staticmethod
    def create_refund(
        db: Session,
        payment_id: UUID,
        amount: float,
        reason: Optional[str] = None
    ) -> Payment:
        """Create a refund for a payment"""
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        
        if not payment:
            raise ValueError(f"Payment {payment_id} not found")
        
        payment.refund_amount = amount
        payment.refund_reason = reason
        payment.refunded_at = datetime.utcnow()
        
        if amount >= payment.amount:
            payment.status = "refunded"
        else:
            payment.status = "partially_refunded"
        
        db.commit()
        db.refresh(payment)
        
        return payment
    
    @staticmethod
    def create_webhook_event(
        db: Session,
        provider: str,
        event_type: str,
        payload: dict,
        provider_event_id: Optional[str] = None,
        signature: Optional[str] = None
    ) -> WebhookEvent:
        """Create a webhook event record"""
        webhook_event = WebhookEvent(
            provider=provider,
            provider_event_id=provider_event_id,
            event_type=event_type,
            payload=payload,
            signature=signature,
            processed=False
        )
        
        db.add(webhook_event)
        db.commit()
        db.refresh(webhook_event)
        
        return webhook_event
    
    @staticmethod
    def mark_webhook_processed(
        db: Session,
        webhook_id: UUID,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> WebhookEvent:
        """Mark webhook as processed"""
        webhook = db.query(WebhookEvent).filter(WebhookEvent.id == webhook_id).first()
        
        if not webhook:
            raise ValueError(f"Webhook event {webhook_id} not found")
        
        webhook.processed = success
        webhook.processed_at = datetime.utcnow()
        
        if error_message:
            webhook.error_message = error_message
        
        db.commit()
        db.refresh(webhook)
        
        return webhook
    
    @staticmethod
    def get_plan(db: Session, plan_id: UUID) -> Optional[Plan]:
        """Get plan by ID"""
        return db.query(Plan).filter(Plan.id == plan_id).first()
    
    @staticmethod
    def get_plan_by_name(db: Session, name: str) -> Optional[Plan]:
        """Get plan by name"""
        return db.query(Plan).filter(Plan.name == name).first()
    
    @staticmethod
    def get_active_plans(db: Session) -> List[Plan]:
        """Get all active plans"""
        return db.query(Plan).filter(Plan.is_active == True).all()


# Singleton instance
db_service = PaymentDatabaseService()