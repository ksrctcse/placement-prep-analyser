
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from app.auth.dependencies import get_db, get_student_user, get_current_user
from app.database.models import User

router = APIRouter(prefix="/student", tags=["Student"])

class StudentDashboardResponse(BaseModel):
    user_id: int
    name: str
    email: str
    department: str
    batch: str
    progress: str
    recommendations: List[str]

@router.get("/dashboard", response_model=StudentDashboardResponse)
async def get_dashboard(current_user: User = Depends(get_student_user)):
    """
    Get student dashboard with progress and recommendations.
    Only accessible to authenticated students.
    """
    recommendations = [
        "Practice system design problems",
        "Review data structures",
        "Work on coding problems on LeetCode",
        "Prepare for behavioral interviews"
    ]
    
    return StudentDashboardResponse(
        user_id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        department=current_user.department if current_user.department else "",
        batch=current_user.batch if current_user.batch else "",
        progress="Good",
        recommendations=recommendations
    )

@router.get("/list")
async def list_students(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all students (accessible to staff only).
    """
    if current_user.role != "staff":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only staff can view student list"
        )
    
    students = db.query(User).filter(User.role == "student").all()
    
    return {
        "total_students": len(students),
        "students": [
            {
                "id": s.id,
                "name": s.name,
                "email": s.email,
                "department": s.department if s.department else None,
                "batch": s.batch if s.batch else None
            }
            for s in students
        ]
    }

@router.get("/{student_id}")
async def get_student_profile(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific student's profile.
    Staff can view any student, students can only view their own.
    """
    student = db.query(User).filter(User.id == student_id).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # Authorization check
    if current_user.role == "student" and current_user.id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own profile"
        )
    
    return {
        "id": student.id,
        "name": student.name,
        "email": student.email,
        "department": student.department if student.department else None,
        "batch": student.batch if student.batch else None,
        "created_at": student.created_at.isoformat()
    }

