from dodopayments import DodoPayments
import hmac
import hashlib
from typing import Dict, Any, Optional
from config import get_settings
from payment_schemas import DodoPaymentRequest, DodoPaymentResponse
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class DodoPaymentService:
    """Service for handling Dodo Payments integration"""
    
    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.dodo_api_key
        self.api_secret = self.settings.dodo_api_secret
        self.webhook_secret = self.settings.dodo_webhook_secret
        # Initialize dodopayments SDK client
        self.client = DodoPayments(
            bearer_token=self.api_key,
            environment="test_mode"  # Change to "production" for live mode
        )
    

    
    def create_payment(
        self, 
        user_id: str,
        user_email: str,
        user_name: str,
        product_id: str,
        quantity: int = 1,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Create a checkout session in Dodo Payments
        Returns checkout session details including checkout URL
        """
        try:
            session = self.client.checkout_sessions.create(
                product_cart=[{"product_id": product_id, "quantity": quantity}],
                customer={
                    "email": user_email,
                    "name": user_name
                },
                return_url=f"{self.settings.webhook_base_url}/payment/success",
                metadata=metadata or {}
            )
            
            return {
                "id": session.id,
                "checkout_url": session.checkout_url,
                "status": session.status
            }
        
        except Exception as e:
            logger.error(f"Dodo payment creation failed: {str(e)}")
            raise Exception(f"Dodo payment creation failed: {str(e)}")
    
    def verify_payment(self, payment_id: str) -> Dict[str, Any]:
        """Verify payment status with Dodo"""
        try:
            payment = self.client.payments.get(payment_id)
            return {
                "id": payment.id,
                "status": payment.status,
                "amount": payment.amount,
                "currency": payment.currency
            }
        
        except Exception as e:
            logger.error(f"Dodo payment verification failed: {str(e)}")
            raise Exception(f"Payment verification failed: {str(e)}")
    
    def create_refund(
        self, 
        payment_id: str, 
        amount: Optional[Decimal] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a refund for a payment"""
        try:
            refund = self.client.refunds.create(
                payment_id=payment_id,
                reason=reason or "Customer requested refund"
            )
            
            return {
                "id": refund.id,
                "payment_id": payment_id,
                "status": refund.status,
                "reason": reason
            }
        
        except Exception as e:
            logger.error(f"Dodo refund creation failed: {str(e)}")
            raise Exception(f"Refund creation failed: {str(e)}")
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify webhook signature from Dodo"""
        try:
            expected_signature = hmac.new(
                self.webhook_secret.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, signature)
        
        except Exception as e:
            logger.error(f"Webhook signature verification failed: {str(e)}")
            return False
    
    def cancel_subscription(self, subscription_id: str, cancel_at_period_end: bool = True) -> Dict[str, Any]:
        """Cancel a subscription in Dodo (scheduled at period end)"""
        try:
            subscription = self.client.subscriptions.update(
                subscription_id,
                cancel_at_period_end=cancel_at_period_end
            )
            
            return {
                "id": subscription.id,
                "status": subscription.status,
                "cancel_at_period_end": cancel_at_period_end
            }
        
        except Exception as e:
            logger.error(f"Dodo subscription cancellation failed: {str(e)}")
            raise Exception(f"Subscription cancellation failed: {str(e)}")
    
    def change_subscription_plan(
        self,
        subscription_id: str,
        product_id: str,
        quantity: int = 1,
        proration_mode: str = "prorated_immediately"
    ) -> Dict[str, Any]:
        """Change subscription plan with proration"""
        try:
            result = self.client.subscriptions.change_plan(
                subscription_id=subscription_id,
                product_id=product_id,
                quantity=quantity,
                proration_billing_mode=proration_mode
            )
            
            return {
                "id": result.id,
                "status": result.status,
                "product_id": product_id
            }
        
        except Exception as e:
            logger.error(f"Dodo subscription plan change failed: {str(e)}")
            raise Exception(f"Subscription plan change failed: {str(e)}")


# Singleton instance
dodo_service = DodoPaymentService()