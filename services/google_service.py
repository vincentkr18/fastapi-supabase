from google.oauth2 import service_account
from googleapiclient.discovery import build
from typing import Dict, Any, Optional
from config import get_settings
import logging
import json

logger = logging.getLogger(__name__)


class GooglePlayService:
    """Service for handling Google Play In-App Purchase verification"""
    
    def __init__(self):
        settings = get_settings()
        self.package_name = settings.google_package_name
        self.service_account_file = settings.google_service_account_json
        self.api_version = settings.google_publisher_api_version
        self._service = None
    
    def _get_service(self):
        """Initialize Google Play Developer API service"""
        if self._service is None:
            try:
                credentials = service_account.Credentials.from_service_account_file(
                    self.service_account_file,
                    scopes=['https://www.googleapis.com/auth/androidpublisher']
                )
                
                self._service = build(
                    'androidpublisher',
                    self.api_version,
                    credentials=credentials,
                    cache_discovery=False
                )
            except Exception as e:
                logger.error(f"Failed to initialize Google Play service: {str(e)}")
                raise
        
        return self._service
    
    async def verify_subscription(self, product_id: str, purchase_token: str) -> Optional[Dict[str, Any]]:
        """
        Verify subscription purchase with Google Play
        Returns subscription details
        """
        try:
            service = self._get_service()
            
            result = service.purchases().subscriptions().get(
                packageName=self.package_name,
                subscriptionId=product_id,
                token=purchase_token
            ).execute()
            
            return result
        
        except Exception as e:
            logger.error(f"Google Play subscription verification failed: {str(e)}")
            return None
    
    async def verify_product(self, product_id: str, purchase_token: str) -> Optional[Dict[str, Any]]:
        """
        Verify one-time product purchase with Google Play
        Returns product details
        """
        try:
            service = self._get_service()
            
            result = service.purchases().products().get(
                packageName=self.package_name,
                productId=product_id,
                token=purchase_token
            ).execute()
            
            return result
        
        except Exception as e:
            logger.error(f"Google Play product verification failed: {str(e)}")
            return None
    
    def parse_subscription(self, subscription_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Google subscription data"""
        return {
            "start_time_ms": subscription_data.get("startTimeMillis"),
            "expiry_time_ms": subscription_data.get("expiryTimeMillis"),
            "auto_renewing": subscription_data.get("autoRenewing", False),
            "payment_state": subscription_data.get("paymentState"),  # 0=pending, 1=received, 2=trial
            "price_currency_code": subscription_data.get("priceCurrencyCode"),
            "price_amount_micros": subscription_data.get("priceAmountMicros"),
            "country_code": subscription_data.get("countryCode"),
            "cancel_reason": subscription_data.get("cancelReason"),  # 0=user, 1=system, 2=replaced
            "user_cancellation_time_ms": subscription_data.get("userCancellationTimeMillis"),
        }
    
    def is_subscription_active(self, expiry_time_ms: str) -> bool:
        """Check if subscription is still active"""
        from datetime import datetime
        
        expiry_timestamp = int(expiry_time_ms) / 1000
        current_timestamp = datetime.utcnow().timestamp()
        
        return current_timestamp < expiry_timestamp
    
    async def acknowledge_purchase(self, product_id: str, purchase_token: str, is_subscription: bool = True) -> bool:
        """
        Acknowledge a purchase with Google Play
        Required within 3 days or purchase will be refunded
        """
        try:
            service = self._get_service()
            
            if is_subscription:
                service.purchases().subscriptions().acknowledge(
                    packageName=self.package_name,
                    subscriptionId=product_id,
                    token=purchase_token
                ).execute()
            else:
                service.purchases().products().acknowledge(
                    packageName=self.package_name,
                    productId=product_id,
                    token=purchase_token
                ).execute()
            
            return True
        
        except Exception as e:
            logger.error(f"Google Play purchase acknowledgment failed: {str(e)}")
            return False
    
    async def refund_subscription(self, product_id: str, purchase_token: str) -> bool:
        """Refund a subscription"""
        try:
            service = self._get_service()
            
            service.purchases().subscriptions().refund(
                packageName=self.package_name,
                subscriptionId=product_id,
                token=purchase_token
            ).execute()
            
            return True
        
        except Exception as e:
            logger.error(f"Google Play refund failed: {str(e)}")
            return False
    
    async def cancel_subscription(self, product_id: str, purchase_token: str) -> bool:
        """Cancel a subscription"""
        try:
            service = self._get_service()
            
            service.purchases().subscriptions().cancel(
                packageName=self.package_name,
                subscriptionId=product_id,
                token=purchase_token
            ).execute()
            
            return True
        
        except Exception as e:
            logger.error(f"Google Play cancellation failed: {str(e)}")
            return False
    
    def verify_webhook_signature(self, payload: str, signature: str, public_key: str) -> bool:
        """
        Verify webhook signature from Google Play
        Google uses base64-encoded signature with RSA-SHA1 or RSA-SHA256
        """
        try:
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import padding
            import base64
            
            # Load public key
            key = serialization.load_pem_public_key(public_key.encode())
            
            # Decode signature
            signature_bytes = base64.b64decode(signature)
            
            # Verify
            key.verify(
                signature_bytes,
                payload.encode(),
                padding.PKCS1v15(),
                hashes.SHA1()
            )
            
            return True
        
        except Exception as e:
            logger.error(f"Google Play webhook signature verification failed: {str(e)}")
            return False


# Singleton instance
google_service = GooglePlayService()