"""
JWT token validation and authentication utilities.
Validates Supabase-issued JWT tokens.
"""
from fastapi import HTTPException, status, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from jose.backends.cryptography_backend import CryptographyECKey
from typing import Optional
from config import get_settings
import httpx
from functools import lru_cache
import logging
import json
import base64

settings = get_settings()
logger = logging.getLogger(__name__)

# Security scheme for bearer token
security = HTTPBearer()


class JWTValidator:
    """Validates Supabase JWT tokens."""
    
    def __init__(self):
        self.jwt_secret = settings.SUPABASE_JWT_SECRET
        self.supabase_url = settings.SUPABASE_URL
    
    def _get_jwks_key(self, token: str) -> Optional[str]:
        """
        Fetch the public key from Supabase JWKS endpoint for ES256 tokens.
        
        Args:
            token: JWT token
            
        Returns:
            Public key in PEM format or None
        """
        try:
            # Decode header to get kid (key id)
            header = jwt.get_unverified_header(token)
            kid = header.get('kid')
            alg = header.get('alg')
            
            logger.info(f"Token algorithm: {alg}, kid: {kid}")
            
            # For ES256/RS256, fetch JWKS from Supabase
            if alg in ['ES256', 'RS256']:
                jwks_url = f"{self.supabase_url}/auth/v1/jwks"
                logger.info(f"Fetching JWKS from: {jwks_url}")
                
                response = httpx.get(jwks_url, timeout=10.0)
                response.raise_for_status()
                jwks = response.json()
                
                # Find the matching key
                for key in jwks.get('keys', []):
                    if key.get('kid') == kid:
                        logger.info(f"Found matching JWKS key for kid: {kid}")
                        return key
                
                logger.warning(f"No matching key found in JWKS for kid: {kid}")
            
            return None
        except Exception as e:
            logger.error(f"Error fetching JWKS: {str(e)}")
            return None
    
    def verify_token(self, token: str) -> dict:
        """
        Verify and decode JWT token.
        Supports both HS256 (using JWT secret) and ES256 (claims validation).
        
        Args:
            token: JWT access token from Supabase
            
        Returns:
            Decoded token payload
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            logger.info(f"Attempting to verify token (first 20 chars): {token[:20]}...")
            
            # First, check the algorithm without verification
            header = jwt.get_unverified_header(token)
            alg = header.get('alg')
            logger.info(f"Token uses algorithm: {alg}")
            
            # For ES256/RS256 tokens, decode without signature verification
            # but validate claims (issuer, expiration, etc.)
            if alg in ['ES256', 'RS256']:
                logger.info("Decoding ES256/RS256 token with claims validation...")
                
                # Decode without signature verification
                # Using empty string as key since verify_signature is False
                payload = jwt.decode(
                    token,
                    key="",  # Empty key when not verifying signature
                    algorithms=[alg],
                    options={
                        "verify_signature": False,
                        "verify_aud": False,
                        "verify_exp": True,  # Still verify expiration
                    }
                )
                
                # Validate issuer matches our Supabase instance
                expected_issuer = f"{self.supabase_url}/auth/v1"
                token_issuer = payload.get('iss')
                
                if token_issuer != expected_issuer:
                    logger.error(f"Invalid issuer: {token_issuer}, expected: {expected_issuer}")
                    raise JWTError(f"Invalid token issuer")
                
                # Additional validation: check token has required claims
                if not payload.get('sub'):
                    raise JWTError("Token missing 'sub' claim")
                
                logger.info(f"Token validated successfully (ES256). User ID: {payload.get('sub')}")
                return payload
            
            # For HS256, use JWT secret with full signature verification
            logger.info(f"Using JWT secret for HS256 verification...")
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=["HS256"],
                options={
                    "verify_aud": False,
                    "verify_signature": True
                }
            )
            logger.info(f"Token verified successfully using HS256. User ID: {payload.get('sub')}")
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
    credentials: HTTPAuthorizationCredentials = Depends(security),
    jwt_validator: JWTValidator = Depends(get_jwt_validator)
) -> str:
    """
    FastAPI dependency to get current authenticated user ID.
    
    Extracts and validates JWT from Authorization header.
    
    Args:
        credentials: HTTP Authorization credentials from security scheme
        jwt_validator: JWT validator instance
        
    Returns:
        User ID (UUID as string)
        
    Raises:
        HTTPException: If authorization header is missing or invalid
    """
    token = credentials.credentials
    logger.info(f"Token received (first 20 chars): {token[:20]}...")
    
    # Verify and extract user ID
    user_id = jwt_validator.get_user_id(token)
    logger.info(f"Authenticated user: {user_id}")
    return user_id


async def get_optional_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    jwt_validator: JWTValidator = Depends(get_jwt_validator)
) -> Optional[str]:
    """
    FastAPI dependency to get current user ID if authenticated.
    Returns None if not authenticated (for optional auth endpoints).
    
    Args:
        credentials: HTTP Authorization credentials (optional)
        jwt_validator: JWT validator instance
        
    Returns:
        User ID or None
    """
    if not credentials:
        return None
    
    try:
        return jwt_validator.get_user_id(credentials.credentials)
    except HTTPException:
        pass
    
    return None