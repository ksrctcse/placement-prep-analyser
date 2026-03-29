from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.auth.jwt_handler import create_token, verify_password, hash_password
from app.database.db import SessionLocal
from app.database.models import User, UserRole, Department, Batch
from app.auth.dependencies import get_db, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Request Models
class StudentSignUpRequest(BaseModel):
    name: str
    email: str
    password: str
    department: str  # CSE, IT, EEE, ECE, MECH, CIVL, CSBS
    batch: str  # 2024-2027 or 2025-2028

class StaffSignUpRequest(BaseModel):
    name: str
    email: str
    password: str
    staff_id: str
    position: str

class LoginRequest(BaseModel):
    email: str
    password: str

# Response Models
class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    role: str
    name: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    department: Optional[str] = None
    batch: Optional[str] = None
    staff_id: Optional[str] = None
    position: Optional[str] = None

    class Config:
        from_attributes = True

# Student Routes
@router.post("/student/signup", response_model=TokenResponse)
def student_signup(request: StudentSignUpRequest, db: Session = Depends(get_db)):
    """
    Student signup endpoint.
    Creates a new student account and returns JWT token.
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate department
    try:
        department = Department[request.department.upper()]
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid department. Valid options: {', '.join([d.value for d in Department])}"
        )
    
    # Validate batch
    try:
        batch = Batch[f"BATCH_{request.batch.replace('-', '_')}"]
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid batch. Valid options: {', '.join([b.value for b in Batch])}"
        )
    
    # Create new user
    hashed_password = hash_password(request.password)
    new_user = User(
        name=request.name,
        email=request.email,
        password=hashed_password,
        role="student",
        department=request.department.upper(),
        batch=request.batch
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Generate token
    token = create_token(user_id=new_user.id, role=new_user.role, email=new_user.email)
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=new_user.id,
        role=new_user.role,
        name=new_user.name
    )

@router.post("/staff/signup", response_model=TokenResponse)
def staff_signup(request: StaffSignUpRequest, db: Session = Depends(get_db)):
    """
    Staff signup endpoint.
    Creates a new staff account and returns JWT token.
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if staff_id is unique
    existing_staff = db.query(User).filter(User.staff_id == request.staff_id).first()
    if existing_staff:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Staff ID already registered"
        )
    
    # Create new staff user
    hashed_password = hash_password(request.password)
    new_user = User(
        name=request.name,
        email=request.email,
        password=hashed_password,
        role="staff",
        staff_id=request.staff_id,
        position=request.position
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Generate token
    token = create_token(user_id=new_user.id, role=new_user.role, email=new_user.email)
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=new_user.id,
        role=new_user.role,
        name=new_user.name
    )

# Common login endpoint for both student and staff
@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Login endpoint for both students and staff.
    Validates credentials and returns JWT token.
    Returns different response based on user role.
    """
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not verify_password(request.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Generate token
    token = create_token(user_id=user.id, role=user.role, email=user.email)
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        role=user.role,
        name=user.name
    )

# Profile endpoints
@router.get("/me", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    """
    Get current user's profile information.
    Requires valid JWT token.
    """
    return current_user

@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """
    Get a user's public profile information.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user
