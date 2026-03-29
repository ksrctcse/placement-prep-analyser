"""
Authentication routes for login and signup
"""
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field
from app.database.db import SessionLocal
from app.database.models import User, StaffProfile, StudentProfile, DepartmentModel, UserRole
import hashlib
import secrets

def hash_password_inline(password: str) -> str:
    """Hash password using PBKDF2 directly in the route"""
    salt = secrets.token_hex(16)
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return f"{salt}${pwdhash.hex()}"

def verify_password_inline(plain: str, hashed: str) -> bool:
    """Verify password using PBKDF2"""
    try:
        salt, pwdhash = hashed.split('$')
        computed = hashlib.pbkdf2_hmac('sha256', plain.encode('utf-8'), salt.encode('utf-8'), 100000)
        return computed.hex() == pwdhash
    except:
        return False

# Import only what we need for token operations
from jose import JWTError, jwt
import os
from datetime import datetime, timedelta

SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

def create_access_token_inline(data: dict, expires_delta = None) -> str:
    """Create JWT token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/test-post")
async def test_post():
    """Simple POST test endpoint"""
    return {"status": "OK", "message": "POST is working"}


@router.get("/test")
async def test_endpoint():
    """Test endpoint to verify API is working"""
    return {"status": "OK", "message": "Auth routes are working"}


@router.post("/test-post")
async def test_post():
    """Simple POST test endpoint"""
    return {"status": "OK", "message": "POST is working"}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Pydantic Models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    role: str
    user_id: int


class StaffSignupRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    department_id: int
    password: str = Field(..., min_length=8)
    confirm_password: str


class StudentSignupRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    department_id: int
    section: str = Field(..., pattern="^[A-C]$")  # A, B, C
    password: str = Field(..., min_length=8)
    confirm_password: str


class DepartmentResponse(BaseModel):
    id: int
    name: str
    
    class Config:
        from_attributes = True


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Login endpoint that returns JWT token"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == request.email).first()
        
        if not user or not verify_password_inline(request.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        
        access_token = create_access_token_inline(
            data={"sub": user.email, "user_id": user.id, "role": user.role.value}
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "role": user.role.value,
            "user_id": user.id
        }
    finally:
        db.close()


@router.post("/staff/signup")
async def staff_signup(request: StaffSignupRequest):
    """Staff signup endpoint"""
    # Validate password match first
    if request.password != request.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )
    
    db = SessionLocal()
    try:
        # Check if email already exists
        existing_user = db.query(User).filter(User.email == request.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Check if department exists
        department = db.query(DepartmentModel).filter(DepartmentModel.id == request.department_id).first()
        if not department:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department not found"
            )
        
        # Create user with inline password hashing
        user = User(
            email=request.email,
            password_hash=hash_password_inline(request.password),
            role=UserRole.STAFF,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create staff profile
        staff_profile = StaffProfile(
            user_id=user.id,
            name=request.name,
            department_id=request.department_id
        )
        db.add(staff_profile)
        db.commit()
        
        return {
            "message": "Staff registered successfully",
            "user_id": user.id,
            "email": user.email
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Signup error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during signup: {str(e)}"
        )
    finally:
        db.close()


@router.post("/student/signup")
async def student_signup(request: StudentSignupRequest):
    """Student signup endpoint"""
    db = SessionLocal()
    try:
        # Validate password match
        if request.password != request.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Passwords do not match"
            )
        
        # Check if email already exists
        existing_user = db.query(User).filter(User.email == request.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Check if department exists
        department = db.query(DepartmentModel).filter(DepartmentModel.id == request.department_id).first()
        if not department:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department not found"
            )
        
        # Create user
        user = User(
            email=request.email,
            password_hash=hash_password_inline(request.password),
            role=UserRole.STUDENT,
            is_active=True
        )
        db.add(user)
        db.flush()
        
        # Create student profile
        student_profile = StudentProfile(
            user_id=user.id,
            name=request.name,
            department_id=request.department_id,
            section=request.section
        )
        db.add(student_profile)
        db.commit()
        
        return {
            "message": "Student registered successfully",
            "user_id": user.id,
            "email": user.email
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error in student_signup: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during signup: {str(e)}"
        )
    finally:
        db.close()


@router.get("/departments", response_model=list[DepartmentResponse])
async def get_departments():
    """Get all departments"""
    db = SessionLocal()
    try:
        departments = db.query(DepartmentModel).all()
        return departments
    finally:
        db.close()


@router.post("/forgot-password")
async def forgot_password(email: str):
    """Forgot password endpoint - sends reset email (simplified)"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            # Don't reveal if email exists or not for security
            return {"message": "If the email exists, a reset link will be sent"}
        
        # In production, generate a reset token and send email
        # For now, just return success message
        return {
            "message": "Password reset link sent to email",
            "email": email
        }
    finally:
        db.close()


@router.get("/verify-token")
async def verify_token(token: str):
    """Verify if a token is valid"""
    try:
        if token.startswith("Bearer "):
            token = token[7:]
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {
            "valid": True,
            "email": payload.get("sub"),
            "user_id": payload.get("user_id"),
            "role": payload.get("role")
        }
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )


@router.post("/logout")
async def logout():
    """Logout endpoint - JWT is stateless, so just return success"""
    return {
        "message": "Logged out successfully",
        "status": "success"
    }
