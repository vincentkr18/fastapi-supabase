"""
JWT token validation and authentication utilities.
Validates Supabase-issued JWT tokens.
"""
from fastapi import HTTPException, status, Depends, Header
from jose import JWTError, jwt
from typing import Optional
from config import get_settings
import httpx
from functools import lru_cache
import logging

settings = get_settings()
logger = logging.getLogger(__name__)


class JWTValidator:
    """Validates Supabase JWT tokens."""
    
    def __init__(self):
        self.jwt_secret = settings.SUPABASE_JWT_SECRET
        self.algorithm = "HS256"
    
    def verify_token(self, token: str) -> dict:
        """
        Verify and decode JWT token.
        
        Args:
            token: JWT access token from Supabase
            
        Returns:
            Decoded token payload
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            logger.info(f"Attempting to verify token (first 20 chars): {token[:20]}...")
            logger.info(f"Using JWT secret (first 10 chars): {self.jwt_secret[:10]}...")
            
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.algorithm],
                options={"verify_aud": False}  # Supabase tokens don't always have audience
            )
            logger.info(f"Token verified successfully. User ID: {payload.get('sub')}")
            return payload
        except JWTError as e:
            logger.error(f"JWT verification failed: {str(e)}")
            logger.error(f"Token: {token[:50]}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid authentication credentials: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def get_user_id(self, token: str) -> str:
        """
        Extract user ID from token.
        
        Args:
            token: JWT access token
            
        Returns:
            User ID (UUID as string)
        """
        payload = self.verify_token(token)
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Print/log user details when valid user detected
        user_email = payload.get("email", "N/A")
        user_role = payload.get("role", "N/A")
        print(f"✓ Valid User Detected:")
        print(f"  - User ID: {user_id}")
        print(f"  - Email: {user_email}")
        print(f"  - Role: {user_role}")
        logger.info(f"Valid user detected - ID: {user_id}, Email: {user_email}, Role: {user_role}")
        
        return user_id


@lru_cache()
def get_jwt_validator() -> JWTValidator:
    """Get cached JWT validator instance."""
    return JWTValidator()


async def get_current_user_id(
    authorization: Optional[str] = Header(None),
    jwt_validator: JWTValidator = Depends(get_jwt_validator)
) -> str:
    """
    FastAPI dependency to get current authenticated user ID.
    
    Extracts and validates JWT from Authorization header.
    
    Args:
        authorization: Authorization header value
        jwt_validator: JWT validator instance
        
    Returns:
        User ID (UUID as string)
        
    Raises:
        HTTPException: If authorization header is missing or invalid
    """
    logger.info(f"Authorization header: {authorization[:50] if authorization else 'None'}...")
    
    if not authorization:
        logger.warning("Missing authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract token from "Bearer <token>"
    scheme, _, token = authorization.partition(" ")
    
    # Print/log the full authorization string
    print(f"📝 Authorization String Received:")
    print(f"  - Full Header: {authorization}")
    print(f"  - Scheme: {scheme}")
    print(f"  - Token: {token}")
    logger.info(f"Authorization - Scheme: {scheme}, Token (first 50 chars): {token[:50] if token else 'None'}...")
    
    if scheme.lower() != "bearer":
        logger.warning(f"Invalid authentication scheme: {scheme}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme. Use 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not token:
        logger.warning("Missing authentication token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify and extract user ID
    user_id = jwt_validator.get_user_id(token)
    logger.info(f"Authenticated user: {user_id}")
    return user_id


async def get_optional_user_id(
    authorization: Optional[str] = Header(None),
    jwt_validator: JWTValidator = Depends(get_jwt_validator)
) -> Optional[str]:
    """
    FastAPI dependency to get current user ID if authenticated.
    Returns None if not authenticated (for optional auth endpoints).
    
    Args:
        authorization: Authorization header value
        jwt_validator: JWT validator instance
        
    Returns:
        User ID or None
    """
    if not authorization:
        return None
    
    try:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() == "bearer" and token:
            return jwt_validator.get_user_id(token)
    except HTTPException:
        pass
    
    return None
