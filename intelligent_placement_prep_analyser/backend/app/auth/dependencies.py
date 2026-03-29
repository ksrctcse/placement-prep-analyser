from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from typing import Optional, Any
from app.auth.jwt_handler import verify_token
from app.database.db import SessionLocal
from app.database.models import User, UserRole
from sqlalchemy.orm import Session

security = HTTPBearer()

def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    credentials: Any = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user.
    Validates the JWT token and returns the user object.
    """
    token = credentials.credentials
    
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id: int = payload.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

def get_student_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to ensure user is a student.
    Use this for protecting student-only endpoints.
    """
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Only students can access this resource."
        )
    return current_user

def get_staff_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to ensure user is staff.
    Use this for protecting staff-only endpoints.
    """
    if current_user.role != UserRole.STAFF:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Only staff can access this resource."
        )
    return current_user

def get_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to ensure user is admin.
    Use this for protecting admin-only endpoints.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Only admins can access this resource."
        )
    return current_user
