import httpx
from typing import Dict, Any, Optional
from config import settings
import logging

logger = logging.getLogger(__name__)


class AppleIAPService:
    """Service for handling Apple In-App Purchase verification"""
    
    def __init__(self):
        self.shared_secret = settings.apple_shared_secret
        self.bundle_id = settings.apple_bundle_id
        self.verify_url = settings.apple_verify_url
    
    async def verify_receipt(self, receipt_data: str) -> Dict[str, Any]:
        """
        Verify receipt with Apple
        Returns receipt validation response
        """
        try:
            payload = {
                "receipt-data": receipt_data,
                "password": self.shared_secret,
                "exclude-old-transactions": False
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.verify_url,
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                
                # If sandbox receipt sent to production, retry with sandbox
                if data.get("status") == 21007 and settings.apple_mode == "production":
                    response = await client.post(
                        settings.apple_verify_receipt_url_sandbox,
                        json=payload,
                        timeout=30.0
                    )
                    response.raise_for_status()
                    data = response.json()
                
                return data
        
        except httpx.HTTPError as e:
            logger.error(f"Apple receipt verification failed: {str(e)}")
            raise Exception(f"Receipt verification failed: {str(e)}")
    
    def parse_receipt(self, receipt_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse Apple receipt data to extract subscription info"""
        try:
            status = receipt_data.get("status")
            
            if status != 0:
                logger.error(f"Apple receipt validation failed with status: {status}")
                return None
            
            # Get latest receipt info
            latest_receipt_info = receipt_data.get("latest_receipt_info", [])
            
            if not latest_receipt_info:
                return None
            
            # Get the most recent transaction
            latest_transaction = max(
                latest_receipt_info,
                key=lambda x: int(x.get("purchase_date_ms", 0))
            )
            
            return {
                "transaction_id": latest_transaction.get("transaction_id"),
                "original_transaction_id": latest_transaction.get("original_transaction_id"),
                "product_id": latest_transaction.get("product_id"),
                "purchase_date_ms": latest_transaction.get("purchase_date_ms"),
                "expires_date_ms": latest_transaction.get("expires_date_ms"),
                "is_trial_period": latest_transaction.get("is_trial_period") == "true",
                "cancellation_date_ms": latest_transaction.get("cancellation_date_ms"),
            }
        
        except Exception as e:
            logger.error(f"Failed to parse Apple receipt: {str(e)}")
            return None
    
    def is_subscription_active(self, expires_date_ms: str, cancellation_date_ms: Optional[str] = None) -> bool:
        """Check if subscription is still active"""
        from datetime import datetime
        
        if cancellation_date_ms:
            return False
        
        expires_timestamp = int(expires_date_ms) / 1000
        current_timestamp = datetime.utcnow().timestamp()
        
        return current_timestamp < expires_timestamp
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify webhook signature from Apple
        Note: Apple uses different signature method - implement based on their docs
        """
        # Apple Server Notifications v2 uses JWT
        # This is a placeholder - implement JWT verification
        logger.warning("Apple webhook signature verification not implemented")
        return True


# Singleton instance
apple_service = AppleIAPService()