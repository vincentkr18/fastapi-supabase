"""
Security utilities for API keys, hashing, etc.
"""
import secrets
import hashlib
from passlib.context import CryptContext
from datetime import datetime, timedelta

# Password hashing context (for API keys)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generate_api_key() -> str:
    """
    Generate a secure random API key.
    
    Returns:
        API key in format: sk_live_<random_string>
    """
    random_bytes = secrets.token_urlsafe(32)
    return f"sk_live_{random_bytes}"


def hash_api_key(api_key: str) -> str:
    """
    Hash an API key using bcrypt.
    
    Args:
        api_key: The API key to hash
        
    Returns:
        Hashed API key
    """
    return pwd_context.hash(api_key)


def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    """
    Verify an API key against its hash.
    
    Args:
        plain_key: The plain text API key
        hashed_key: The hashed API key
        
    Returns:
        True if the key matches
    """
    return pwd_context.verify(plain_key, hashed_key)


def get_api_key_prefix(api_key: str, length: int = 8) -> str:
    """
    Get the prefix of an API key for display purposes.
    
    Args:
        api_key: The full API key
        length: Number of characters to include in prefix
        
    Returns:
        Key prefix (e.g., "sk_live_...")
    """
    if len(api_key) <= length:
        return api_key
    return f"{api_key[:length]}..."


def verify_webhook_signature(payload: str, signature: str, secret: str) -> bool:
    """
    Verify webhook signature from Lemon Squeezy.
    
    Args:
        payload: The raw webhook payload
        signature: The signature from webhook headers
        secret: The webhook secret
        
    Returns:
        True if signature is valid
    """
    computed_signature = hashlib.sha256(
        f"{payload}{secret}".encode()
    ).hexdigest()
    
    return secrets.compare_digest(computed_signature, signature)
