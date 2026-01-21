from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Annotated
from uuid import UUID
from datetime import datetime, timedelta

from payment_schemas import (
    PaymentResponse,
    SubscriptionResponse,
    DodoPaymentRequest,
    DodoPaymentResponse,
    AppleReceiptValidation,
    GooglePurchaseToken,
    CancelSubscriptionRequest,
    RefundRequest,
    PlanResponse
)
from services.dodo_service import dodo_service
from services.apple_service import apple_service
from services.google_service import google_service
from services.db_service import db_service
from database import get_db
from utils.auth import get_current_user_id
from models import Plan
from database import get_supabase


router = APIRouter(prefix="/api/payments", tags=["payments"])


# ============================================================================
# DODO PAYMENTS (WEB)
# ============================================================================

@router.post("/dodo/create", response_model=DodoPaymentResponse)
async def create_dodo_payment(
    request: DodoPaymentRequest,
    db: Session = Depends(get_db),
    current_user_id: Annotated[str, Depends(get_current_user_id)] = None
):
    """Create a new payment via Dodo Payments (Web)"""
    try:
        # Get plan details
        plan = db_service.get_plan(db, request.plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        # Get Dodo product_id from plan
        product_id = plan.provider_ids.get("dodo")
        if not product_id:
            raise HTTPException(status_code=400, detail="Plan not configured for Dodo Payments")
        
        # Get user email from metadata or use user_id as fallback
        # user_email = request.metadata.get("user_email", f"{current_user_id}@temp.com")
        # user_name = request.metadata.get("user_name", "Customer")
        supabase = get_supabase()
    
        response = supabase.auth.admin.get_user_by_id(current_user_id)
        user_email = response.user.email
        user_name  = user_email.split('@')[0]

        # Create checkout session in Dodo
        payment_data = dodo_service.create_payment(
            user_id=current_user_id,
            user_email=user_email,
            user_name=user_name,
            product_id=product_id,
            quantity=1,
            metadata=request.metadata
        )
        
        # Get amount from plan pricing
        amount = plan.pricing.get("monthly_usd", 0)
        
        # Create payment record in DB
        db_service.create_payment(
            db=db,
            user_id=UUID(current_user_id),
            provider="dodo",
            provider_payment_id=payment_data["id"],
            amount=amount,
            currency="USD",
            metadata={
                "plan_id": str(request.plan_id),
                "checkout_url": payment_data.get("checkout_url"),
                **request.metadata
            }
        )
        
        return DodoPaymentResponse(
            payment_id=payment_data["id"],
            checkout_url=payment_data["checkout_url"],
            amount=amount,
            currency="USD",
            status=payment_data["status"]
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dodo/verify/{payment_id}")
async def verify_dodo_payment(
    payment_id: str,
    db: Session = Depends(get_db),
    current_user_id: Annotated[str, Depends(get_current_user_id)] = None
):
    """Verify a Dodo payment status"""
    try:
        payment_data = dodo_service.verify_payment(payment_id)
        
        # Update payment in DB
        payment = db_service.get_payment_by_provider_id(db, payment_id)
        if payment:
            if payment_data["status"] == "completed":
                db_service.update_payment_status(
                    db, payment.id, "completed", datetime.utcnow()
                )
        
        return {"status": payment_data["status"], "data": payment_data}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/checkout-url")
async def get_checkout_url(
    request: DodoPaymentRequest,
    db: Session = Depends(get_db),
    current_user_id: Annotated[str, Depends(get_current_user_id)] = None
):
    """Get checkout URL for a plan (simplified endpoint)"""
    try:
        # Get plan details
        plan = db_service.get_plan(db, request.plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        print(type(request.metadata))
        # Get Dodo product_id from plan
        if request.metadata['billing_cycle'] == 'monthly':
            product_id = plan.provider_ids.get("dodo_monthly")
        else:
            product_id = plan.provider_ids.get("dodo_yearly")
        if not product_id:
            raise HTTPException(status_code=400, detail="Plan not configured for Dodo Payments")
        
        # Get user email from metadata or use user_id as fallback
       
        supabase = get_supabase()
    
        response = supabase.auth.admin.get_user_by_id(current_user_id)
        user_email = response.user.email
        user_name  = user_email.split('@')[0]

        
        print(current_user_id, user_email, user_name)
        # Create checkout session in Dodo
        payment_data = dodo_service.create_payment(
            user_id=current_user_id,
            user_email=user_email,
            user_name=user_name,
            product_id=product_id,
            quantity=1,
            metadata=request.metadata
        )
        
        return {
            "checkout_url": payment_data["checkout_url"],
            "payment_id": payment_data["id"]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/customer-portal")
async def get_customer_portal(
    send_email: bool = False,
    db: Session = Depends(get_db),
    current_user_id: Annotated[str, Depends(get_current_user_id)] = None
):
    """Get customer portal URL for managing subscriptions"""
    try:
        # Get user email from Supabase
        supabase = get_supabase()
        response = supabase.auth.admin.get_user_by_id(current_user_id)
        user_email = response.user.email
        
        # Get customer ID from Dodo Payments
        customer_id = dodo_service.get_customer_by_email(user_email)
        
        if not customer_id:
            raise HTTPException(
                status_code=404,
                detail="Customer not found. Please create a subscription first."
            )
        
        # Create customer portal session
        portal_data = dodo_service.create_customer_portal(
            customer_id=customer_id,
            send_email=send_email
        )
        
        return {
            "portal_url": portal_data["portal_url"],
            "customer_id": customer_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# APPLE IAP (iOS)
# ============================================================================

@router.post("/apple/verify")
async def verify_apple_receipt(
    request: AppleReceiptValidation,
    db: Session = Depends(get_db),
    current_user_id: Annotated[str, Depends(get_current_user_id)] = None
):
    """Verify Apple receipt and create/update subscription"""
    try:
        # Verify receipt with Apple
        receipt_data = await apple_service.verify_receipt(request.receipt_data)
        
        if receipt_data.get("status") != 0:
            raise HTTPException(
                status_code=400,
                detail=f"Receipt validation failed: {receipt_data.get('status')}"
            )
        
        # Parse receipt
        subscription_info = apple_service.parse_receipt(receipt_data)
        if not subscription_info:
            raise HTTPException(status_code=400, detail="Invalid receipt data")
        
        # Get or create subscription
        existing_sub = db_service.get_subscription_by_provider_id(
            db, subscription_info["original_transaction_id"]
        )
        
        if existing_sub:
            # Update existing subscription
            is_active = apple_service.is_subscription_active(
                subscription_info["expires_date_ms"],
                subscription_info.get("cancellation_date_ms")
            )
            
            status = "active" if is_active else "expired"
            db_service.update_subscription_status(
                db, existing_sub.id, status, "renewed", subscription_info
            )
            
            return {"subscription_id": str(existing_sub.id), "status": status}
        
        else:
            # Find plan by Apple product ID
            # You'll need to map Apple product IDs to your plans
            plan = db.query(Plan).filter(
                Plan.provider_ids["apple"].astext == subscription_info["product_id"]
            ).first()
            
            if not plan:
                raise HTTPException(status_code=404, detail="Plan not found for product")
            
            # Create new subscription
            expires_timestamp = int(subscription_info["expires_date_ms"]) / 1000
            expires_date = datetime.fromtimestamp(expires_timestamp)
            
            purchase_timestamp = int(subscription_info["purchase_date_ms"]) / 1000
            purchase_date = datetime.fromtimestamp(purchase_timestamp)
            
            subscription = db_service.create_subscription(
                db=db,
                user_id=UUID(current_user_id),
                plan_id=plan.id,
                provider="apple",
                provider_subscription_id=subscription_info["original_transaction_id"],
                current_period_start=purchase_date,
                current_period_end=expires_date,
                trial_end=None
            )
            
            # Create payment record
            db_service.create_payment(
                db=db,
                user_id=UUID(current_user_id),
                provider="apple",
                provider_payment_id=subscription_info["transaction_id"],
                amount=0,  # Apple doesn't provide amount in receipt
                currency="USD",
                subscription_id=subscription.id,
                metadata=subscription_info
            )
            
            return {"subscription_id": str(subscription.id), "status": "active"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# GOOGLE PLAY (ANDROID)
# ============================================================================

@router.post("/google/verify")
async def verify_google_purchase(
    request: GooglePurchaseToken,
    db: Session = Depends(get_db),
    current_user_id: Annotated[str, Depends(get_current_user_id)] = None
):
    """Verify Google Play purchase and create/update subscription"""
    try:
        # Verify with Google Play
        if request.subscription:
            purchase_data = await google_service.verify_subscription(
                request.product_id,
                request.purchase_token
            )
        else:
            purchase_data = await google_service.verify_product(
                request.product_id,
                request.purchase_token
            )
        
        if not purchase_data:
            raise HTTPException(status_code=400, detail="Purchase verification failed")
        
        # Acknowledge purchase (required by Google)
        await google_service.acknowledge_purchase(
            request.product_id,
            request.purchase_token,
            request.subscription
        )
        
        if request.subscription:
            subscription_info = google_service.parse_subscription(purchase_data)
            
            # Check if subscription exists
            # Use purchase token as unique identifier
            existing_sub = db_service.get_subscription_by_provider_id(
                db, request.purchase_token
            )
            
            if existing_sub:
                # Update existing
                is_active = google_service.is_subscription_active(
                    subscription_info["expiry_time_ms"]
                )
                
                status = "active" if is_active else "expired"
                db_service.update_subscription_status(
                    db, existing_sub.id, status, "renewed", subscription_info
                )
                
                return {"subscription_id": str(existing_sub.id), "status": status}
            
            else:
                # Find plan by Google product ID
                plan = db.query(Plan).filter(
                    Plan.provider_ids["google"].astext == request.product_id
                ).first()
                
                if not plan:
                    raise HTTPException(status_code=404, detail="Plan not found")
                
                # Create subscription
                start_timestamp = int(subscription_info["start_time_ms"]) / 1000
                start_date = datetime.fromtimestamp(start_timestamp)
                
                expiry_timestamp = int(subscription_info["expiry_time_ms"]) / 1000
                expiry_date = datetime.fromtimestamp(expiry_timestamp)
                
                subscription = db_service.create_subscription(
                    db=db,
                    user_id=UUID(current_user_id),
                    plan_id=plan.id,
                    provider="google",
                    provider_subscription_id=request.purchase_token,
                    current_period_start=start_date,
                    current_period_end=expiry_date
                )
                
                # Create payment record
                amount_micros = int(subscription_info.get("price_amount_micros", 0))
                amount = amount_micros / 1000000  # Convert micros to standard
                
                db_service.create_payment(
                    db=db,
                    user_id=UUID(current_user_id),
                    provider="google",
                    provider_payment_id=request.purchase_token,
                    amount=amount,
                    currency=subscription_info.get("price_currency_code", "USD"),
                    subscription_id=subscription.id,
                    metadata=subscription_info
                )
                
                return {"subscription_id": str(subscription.id), "status": "active"}
        
        else:
            # Handle one-time product purchase
            # Similar logic but no subscription
            pass
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SUBSCRIPTION MANAGEMENT
# ============================================================================

@router.get("/subscriptions", response_model=List[SubscriptionResponse])
async def get_user_subscriptions(
    active_only: bool = False,
    db: Session = Depends(get_db),
    current_user_id: Annotated[str, Depends(get_current_user_id)] = None
):
    """Get all subscriptions for current user"""
    print(current_user_id)
    subscriptions = db_service.get_user_subscriptions(
        db, UUID(current_user_id), active_only
    )
    return subscriptions


@router.get("/subscriptions/{subscription_id}", response_model=SubscriptionResponse)
async def get_subscription(
    subscription_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: Annotated[str, Depends(get_current_user_id)] = None
):
    """Get specific subscription"""
    subscription = db_service.get_subscription(db, subscription_id)
    
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    if subscription.user_id != UUID(current_user_id):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return subscription


@router.post("/subscriptions/{subscription_id}/cancel")
async def cancel_subscription(
    subscription_id: UUID,
    request: CancelSubscriptionRequest,
    db: Session = Depends(get_db),
    current_user_id: Annotated[str, Depends(get_current_user_id)] = None
):
    """Cancel a subscription"""
    subscription = db_service.get_subscription(db, subscription_id)
    
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    if subscription.user_id != UUID(current_user_id):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        # Cancel with provider
        if subscription.provider == "dodo":
            dodo_service.cancel_subscription(
                subscription.provider_subscription_id,
                cancel_at_period_end=request.cancel_at_period_end
            )
        elif subscription.provider == "google":
            plan = db_service.get_plan(db, subscription.plan_id)
            product_id = plan.provider_ids.get("google")
            await google_service.cancel_subscription(
                product_id, subscription.provider_subscription_id
            )
        # Apple subscriptions are canceled by user in App Store
        
        # Update in database
        db_service.cancel_subscription(
            db, subscription_id, request.cancel_at_period_end, request.reason
        )
        
        return {"message": "Subscription canceled successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# REFUNDS
# ============================================================================

@router.post("/refunds")
async def create_refund(
    request: RefundRequest,
    db: Session = Depends(get_db),
    current_user_id: Annotated[str, Depends(get_current_user_id)] = None  # Should have admin check
):
    """Create a refund (admin only)"""
    payment = db_service.get_payment_by_provider_id(db, str(request.payment_id))
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    try:
        if payment.provider == "dodo":
            dodo_service.create_refund(
                payment.provider_payment_id,
                request.amount,
                request.reason
            )
        elif payment.provider == "google":
            # Google refunds
            subscription = db_service.get_subscription(db, payment.subscription_id)
            plan = db_service.get_plan(db, subscription.plan_id)
            product_id = plan.provider_ids.get("google")
            
            await google_service.refund_subscription(
                product_id,
                subscription.provider_subscription_id
            )
        # Apple refunds handled through App Store Connect
        
        # Update database
        refund_amount = request.amount or payment.amount
        db_service.create_refund(db, payment.id, refund_amount, request.reason)
        
        return {"message": "Refund created successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PLANS
# ============================================================================

@router.get("/plans", response_model=List[PlanResponse])
async def get_plans(db: Session = Depends(get_db)):
    """Get all active plans"""
    plans = db_service.get_active_plans(db)
    return plans