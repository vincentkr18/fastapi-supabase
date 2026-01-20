from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from services.dodo_service import dodo_service
from services.apple_service import apple_service
from services.google_service import google_service
from services.db_service import db_service
from database import get_db
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


# ============================================================================
# DODO WEBHOOKS
# ============================================================================

@router.post("/dodo")
async def dodo_webhook(
    request: Request,
    db: Session = Depends(get_db),
    signature: Optional[str] = Header(None, alias="X-Dodo-Signature")
):
    """Handle webhooks from Dodo Payments"""
    try:
        # Get raw body for signature verification
        body = await request.body()
        
        # Verify signature
        if not dodo_service.verify_webhook_signature(body, signature):
            logger.warning("Invalid Dodo webhook signature")
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Parse payload
        payload = json.loads(body.decode())
        event_type = payload.get("type")
        event_data = payload.get("data", {})
        
        # Store webhook event
        webhook_event = db_service.create_webhook_event(
            db=db,
            provider="dodo",
            event_type=event_type,
            payload=payload,
            provider_event_id=payload.get("id"),
            signature=signature
        )
        
        try:
            # Process different event types
            if event_type == "payment.succeeded":
                await handle_dodo_payment_succeeded(db, event_data)
            
            elif event_type == "payment.failed":
                await handle_dodo_payment_failed(db, event_data)
            
            elif event_type == "subscription.created":
                await handle_dodo_subscription_created(db, event_data)
            
            elif event_type == "subscription.renewed":
                await handle_dodo_subscription_renewed(db, event_data)
            
            elif event_type == "subscription.canceled":
                await handle_dodo_subscription_canceled(db, event_data)
            
            elif event_type == "subscription.expired":
                await handle_dodo_subscription_expired(db, event_data)
            
            elif event_type == "refund.created":
                await handle_dodo_refund_created(db, event_data)
            
            else:
                logger.info(f"Unhandled Dodo event type: {event_type}")
            
            # Mark webhook as processed
            db_service.mark_webhook_processed(db, webhook_event.id, success=True)
            
            return {"status": "success"}
        
        except Exception as e:
            logger.error(f"Error processing Dodo webhook: {str(e)}")
            db_service.mark_webhook_processed(
                db, webhook_event.id, success=False, error_message=str(e)
            )
            raise
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dodo webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def handle_dodo_payment_succeeded(db: Session, data: dict):
    """Handle successful payment from Dodo"""
    payment_id = data.get("payment_id")
    
    payment = db_service.get_payment_by_provider_id(db, payment_id)
    if payment:
        db_service.update_payment_status(db, payment.id, "completed", datetime.utcnow())
        
        # If this is for a subscription, activate it
        if payment.subscription_id:
            subscription = db_service.get_subscription(db, payment.subscription_id)
            if subscription and subscription.status != "active":
                db_service.update_subscription_status(
                    db, subscription.id, "active", "payment_succeeded", data
                )


async def handle_dodo_payment_failed(db: Session, data: dict):
    """Handle failed payment from Dodo"""
    payment_id = data.get("payment_id")
    
    payment = db_service.get_payment_by_provider_id(db, payment_id)
    if payment:
        db_service.update_payment_status(db, payment.id, "failed", None)
        
        # If this is for a subscription, mark as past_due
        if payment.subscription_id:
            subscription = db_service.get_subscription(db, payment.subscription_id)
            if subscription:
                db_service.update_subscription_status(
                    db, subscription.id, "past_due", "payment_failed", data
                )


async def handle_dodo_subscription_created(db: Session, data: dict):
    """Handle subscription creation from Dodo"""
    subscription_id = data.get("subscription_id")
    customer_id = data.get("customer_id")
    plan_id = data.get("plan_id")
    
    # Find user by customer_id (you may need to adjust this)
    # For now, logging the event
    logger.info(f"Dodo subscription created: {subscription_id}")


async def handle_dodo_subscription_renewed(db: Session, data: dict):
    """Handle subscription renewal from Dodo"""
    subscription_id = data.get("subscription_id")
    
    subscription = db_service.get_subscription_by_provider_id(db, subscription_id)
    if subscription:
        # Update period end
        new_period_end = datetime.fromisoformat(data.get("current_period_end"))
        subscription.current_period_end = new_period_end
        
        db_service.update_subscription_status(
            db, subscription.id, "active", "renewed", data
        )


async def handle_dodo_subscription_canceled(db: Session, data: dict):
    """Handle subscription cancellation from Dodo"""
    subscription_id = data.get("subscription_id")
    
    subscription = db_service.get_subscription_by_provider_id(db, subscription_id)
    if subscription:
        db_service.cancel_subscription(
            db, subscription.id, 
            cancel_at_period_end=data.get("cancel_at_period_end", True),
            reason=data.get("reason")
        )


async def handle_dodo_subscription_expired(db: Session, data: dict):
    """Handle subscription expiration from Dodo"""
    subscription_id = data.get("subscription_id")
    
    subscription = db_service.get_subscription_by_provider_id(db, subscription_id)
    if subscription:
        db_service.update_subscription_status(
            db, subscription.id, "expired", "expired", data
        )


async def handle_dodo_refund_created(db: Session, data: dict):
    """Handle refund creation from Dodo"""
    payment_id = data.get("payment_id")
    refund_amount = data.get("amount")
    
    payment = db_service.get_payment_by_provider_id(db, payment_id)
    if payment:
        db_service.create_refund(
            db, payment.id, refund_amount, data.get("reason")
        )


# ============================================================================
# APPLE WEBHOOKS (Server Notifications v2)
# ============================================================================

@router.post("/apple")
async def apple_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle Apple App Store Server Notifications"""
    try:
        body = await request.body()
        payload = json.loads(body.decode())
        
        # Apple sends JWT signed payloads in v2
        # You'll need to verify the JWT signature
        # For now, we'll log and process
        
        signed_payload = payload.get("signedPayload")
        
        # Store webhook event
        webhook_event = db_service.create_webhook_event(
            db=db,
            provider="apple",
            event_type=payload.get("notificationType", "unknown"),
            payload=payload,
            provider_event_id=None
        )
        
        try:
            # Decode JWT and extract data
            # This is simplified - implement proper JWT verification
            notification_type = payload.get("notificationType")
            
            if notification_type == "SUBSCRIBED":
                await handle_apple_subscribed(db, payload)
            
            elif notification_type == "DID_RENEW":
                await handle_apple_renewed(db, payload)
            
            elif notification_type == "DID_CHANGE_RENEWAL_STATUS":
                await handle_apple_renewal_status_changed(db, payload)
            
            elif notification_type == "EXPIRED":
                await handle_apple_expired(db, payload)
            
            elif notification_type == "REFUND":
                await handle_apple_refund(db, payload)
            
            else:
                logger.info(f"Unhandled Apple notification: {notification_type}")
            
            db_service.mark_webhook_processed(db, webhook_event.id, success=True)
            
            return {"status": "success"}
        
        except Exception as e:
            logger.error(f"Error processing Apple webhook: {str(e)}")
            db_service.mark_webhook_processed(
                db, webhook_event.id, success=False, error_message=str(e)
            )
            raise
    
    except Exception as e:
        logger.error(f"Apple webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def handle_apple_subscribed(db: Session, data: dict):
    """Handle new subscription from Apple"""
    logger.info("Apple subscription created")
    # Extract transaction info from JWT payload and process


async def handle_apple_renewed(db: Session, data: dict):
    """Handle subscription renewal from Apple"""
    logger.info("Apple subscription renewed")


async def handle_apple_renewal_status_changed(db: Session, data: dict):
    """Handle renewal status change from Apple"""
    logger.info("Apple renewal status changed")


async def handle_apple_expired(db: Session, data: dict):
    """Handle subscription expiration from Apple"""
    logger.info("Apple subscription expired")


async def handle_apple_refund(db: Session, data: dict):
    """Handle refund from Apple"""
    logger.info("Apple refund processed")


# ============================================================================
# GOOGLE PLAY WEBHOOKS (Real-time Developer Notifications)
# ============================================================================

@router.post("/google")
async def google_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle Google Play Real-time Developer Notifications"""
    try:
        body = await request.body()
        payload = json.loads(body.decode())
        
        # Google sends base64-encoded Pub/Sub messages
        message = payload.get("message", {})
        data = message.get("data")
        
        # Decode base64 data
        import base64
        decoded_data = json.loads(base64.b64decode(data).decode())
        
        # Store webhook event
        webhook_event = db_service.create_webhook_event(
            db=db,
            provider="google",
            event_type=decoded_data.get("notificationType", "unknown"),
            payload=decoded_data,
            provider_event_id=message.get("messageId")
        )
        
        try:
            notification_type = decoded_data.get("notificationType")
            
            # Subscription notifications (1-13)
            if notification_type == 1:  # SUBSCRIPTION_RECOVERED
                await handle_google_subscription_recovered(db, decoded_data)
            
            elif notification_type == 2:  # SUBSCRIPTION_RENEWED
                await handle_google_subscription_renewed(db, decoded_data)
            
            elif notification_type == 3:  # SUBSCRIPTION_CANCELED
                await handle_google_subscription_canceled(db, decoded_data)
            
            elif notification_type == 4:  # SUBSCRIPTION_PURCHASED
                await handle_google_subscription_purchased(db, decoded_data)
            
            elif notification_type == 5:  # SUBSCRIPTION_ON_HOLD
                await handle_google_subscription_on_hold(db, decoded_data)
            
            elif notification_type == 6:  # SUBSCRIPTION_IN_GRACE_PERIOD
                await handle_google_subscription_grace_period(db, decoded_data)
            
            elif notification_type == 12:  # SUBSCRIPTION_EXPIRED
                await handle_google_subscription_expired(db, decoded_data)
            
            elif notification_type == 13:  # SUBSCRIPTION_PAUSED
                await handle_google_subscription_paused(db, decoded_data)
            
            else:
                logger.info(f"Unhandled Google notification: {notification_type}")
            
            db_service.mark_webhook_processed(db, webhook_event.id, success=True)
            
            return {"status": "success"}
        
        except Exception as e:
            logger.error(f"Error processing Google webhook: {str(e)}")
            db_service.mark_webhook_processed(
                db, webhook_event.id, success=False, error_message=str(e)
            )
            raise
    
    except Exception as e:
        logger.error(f"Google webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def handle_google_subscription_purchased(db: Session, data: dict):
    """Handle new subscription purchase from Google"""
    subscription_notification = data.get("subscriptionNotification", {})
    purchase_token = subscription_notification.get("purchaseToken")
    
    logger.info(f"Google subscription purchased: {purchase_token}")


async def handle_google_subscription_renewed(db: Session, data: dict):
    """Handle subscription renewal from Google"""
    subscription_notification = data.get("subscriptionNotification", {})
    purchase_token = subscription_notification.get("purchaseToken")
    
    subscription = db_service.get_subscription_by_provider_id(db, purchase_token)
    if subscription:
        # Verify with Google to get updated expiry
        product_id = subscription_notification.get("subscriptionId")
        purchase_data = await google_service.verify_subscription(product_id, purchase_token)
        
        if purchase_data:
            subscription_info = google_service.parse_subscription(purchase_data)
            
            expiry_timestamp = int(subscription_info["expiry_time_ms"]) / 1000
            new_period_end = datetime.fromtimestamp(expiry_timestamp)
            
            subscription.current_period_end = new_period_end
            db_service.update_subscription_status(
                db, subscription.id, "active", "renewed", subscription_info
            )


async def handle_google_subscription_canceled(db: Session, data: dict):
    """Handle subscription cancellation from Google"""
    subscription_notification = data.get("subscriptionNotification", {})
    purchase_token = subscription_notification.get("purchaseToken")
    
    subscription = db_service.get_subscription_by_provider_id(db, purchase_token)
    if subscription:
        db_service.cancel_subscription(db, subscription.id, cancel_at_period_end=True)


async def handle_google_subscription_expired(db: Session, data: dict):
    """Handle subscription expiration from Google"""
    subscription_notification = data.get("subscriptionNotification", {})
    purchase_token = subscription_notification.get("purchaseToken")
    
    subscription = db_service.get_subscription_by_provider_id(db, purchase_token)
    if subscription:
        db_service.update_subscription_status(
            db, subscription.id, "expired", "expired", data
        )


async def handle_google_subscription_recovered(db: Session, data: dict):
    """Handle subscription recovery from Google"""
    subscription_notification = data.get("subscriptionNotification", {})
    purchase_token = subscription_notification.get("purchaseToken")
    
    subscription = db_service.get_subscription_by_provider_id(db, purchase_token)
    if subscription:
        db_service.update_subscription_status(
            db, subscription.id, "active", "recovered", data
        )


async def handle_google_subscription_on_hold(db: Session, data: dict):
    """Handle subscription on hold from Google"""
    logger.info("Google subscription on hold")


async def handle_google_subscription_grace_period(db: Session, data: dict):
    """Handle subscription in grace period from Google"""
    subscription_notification = data.get("subscriptionNotification", {})
    purchase_token = subscription_notification.get("purchaseToken")
    
    subscription = db_service.get_subscription_by_provider_id(db, purchase_token)
    if subscription:
        db_service.update_subscription_status(
            db, subscription.id, "past_due", "grace_period", data
        )


async def handle_google_subscription_paused(db: Session, data: dict):
    """Handle subscription pause from Google"""
    logger.info("Google subscription paused")