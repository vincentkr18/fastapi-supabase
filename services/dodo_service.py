import httpx
import hmac
import hashlib
from typing import Dict, Any, Optional
from config import settings
from schemas import DodoPaymentRequest, DodoPaymentResponse
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class DodoPaymentService:
    """Service for handling Dodo Payments integration"""
    
    def __init__(self):
        self.api_key = settings.dodo_api_key
        self.api_secret = settings.dodo_api_secret
        self.base_url = settings.dodo_base_url
        self.webhook_secret = settings.dodo_webhook_secret
    
    def _get_headers(self) -> Dict[str, str]:
        """Get API headers for Dodo Payments"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def create_payment(
        self, 
        user_id: str, 
        amount: Decimal, 
        currency: str,
        plan_id: str,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Create a payment in Dodo Payments
        Returns payment details including checkout URL
        """
        try:
            payload = {
                "amount": float(amount),
                "currency": currency,
                "customer": {
                    "id": user_id
                },
                "metadata": metadata or {},
                "return_url": f"{settings.webhook_base_url}/payment/success",
                "cancel_url": f"{settings.webhook_base_url}/payment/cancel"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/payments",
                    headers=self._get_headers(),
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
        
        except httpx.HTTPError as e:
            logger.error(f"Dodo payment creation failed: {str(e)}")
            raise Exception(f"Payment creation failed: {str(e)}")
    
    async def verify_payment(self, payment_id: str) -> Dict[str, Any]:
        """Verify payment status with Dodo"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/payments/{payment_id}",
                    headers=self._get_headers(),
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
        
        except httpx.HTTPError as e:
            logger.error(f"Dodo payment verification failed: {str(e)}")
            raise Exception(f"Payment verification failed: {str(e)}")
    
    async def create_refund(
        self, 
        payment_id: str, 
        amount: Optional[Decimal] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a refund for a payment"""
        try:
            payload = {
                "payment_id": payment_id,
                "reason": reason or "Customer requested"
            }
            
            if amount:
                payload["amount"] = float(amount)
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/refunds",
                    headers=self._get_headers(),
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
        
        except httpx.HTTPError as e:
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
    
    async def cancel_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Cancel a subscription in Dodo"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/subscriptions/{subscription_id}/cancel",
                    headers=self._get_headers(),
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
        
        except httpx.HTTPError as e:
            logger.error(f"Dodo subscription cancellation failed: {str(e)}")
            raise Exception(f"Subscription cancellation failed: {str(e)}")


# Singleton instance
dodo_service = DodoPaymentService()