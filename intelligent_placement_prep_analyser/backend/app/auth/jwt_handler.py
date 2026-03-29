
from jose import jwt, JWTError
from datetime import datetime, timedelta
from app.config.settings import settings
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from typing import Optional, Dict, Any

# Argon2 password hasher - more modern than bcrypt, no compatibility issues
hasher = PasswordHasher()

def hash_password(password: str) -> str:
    """Hash a password using Argon2."""
    return hasher.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash."""
    try:
        hasher.verify(hashed_password, plain_password)
        return True
    except VerifyMismatchError:
        return False

def create_token(user_id: int, role: str, email: str, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT token with user information.
    
    Args:
        user_id: The user's ID
        role: The user's role (student, staff, admin)
        email: The user's email
        expires_delta: Optional custom expiration time
    
    Returns:
        JWT token string
    """
    if expires_delta is None:
        expires_delta = timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    
    expire = datetime.utcnow() + expires_delta
    
    payload = {
        "user_id": user_id,
        "role": role,
        "email": email,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def verify_token(token: str) -> Dict[str, Any]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded token payload
    
    Raises:
        JWTError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None
