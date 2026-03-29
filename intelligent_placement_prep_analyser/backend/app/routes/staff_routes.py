
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from app.auth.dependencies import get_db, get_staff_user, get_current_user
from app.database.models import User, InterviewReport

router = APIRouter(prefix="/staff", tags=["Staff"])

class StudentProgressItem(BaseModel):
    id: int
    name: str
    email: str
    department: Optional[str]
    batch: Optional[str]
    interview_score: Optional[int] = None

class StaffDashboardResponse(BaseModel):
    total_students: int
    total_staff: int
    top_performers: List[StudentProgressItem]

@router.get("/dashboard")
async def get_staff_dashboard(
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db)
):
    """
    Get staff dashboard with overall statistics.
    Only accessible to staff members.
    """
    # Get student statistics
    total_students = db.query(User).filter(User.role == "student").count()
    total_staff = db.query(User).filter(User.role == "staff").count()
    
    # Get top performers (students with highest interview scores)
    top_performers = db.query(User).outerjoin(InterviewReport).filter(
        User.role == "student"
    ).all()[:5]
    
    return {
        "staff_name": current_user.name,
        "position": current_user.position,
        "total_students": total_students,
        "total_staff": total_staff,
        "message": "Staff dashboard loaded successfully"
    }

@router.get("/students-progress")
async def get_students_progress(
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db)
):
    """
    Get progress of all students.
    Only accessible to staff members.
    """
    students = db.query(User).filter(User.role == "student").all()
    
    students_data = []
    for student in students:
        # Get latest interview report for student
        latest_report = db.query(InterviewReport).filter(
            InterviewReport.user_id == student.id
        ).order_by(InterviewReport.created_at.desc()).first()
        
        students_data.append({
            "id": student.id,
            "name": student.name,
            "email": student.email,
            "department": student.department if student.department else None,
            "batch": student.batch if student.batch else None,
            "score": latest_report.score if latest_report else None,
            "feedback": latest_report.feedback if latest_report else None
        })
    
    return {
        "total_students": len(students_data),
        "students": students_data
    }

@router.get("/students-by-department/{department}")
async def get_students_by_department(
    department: str,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db)
):
    """
    Get students filtered by department.
    Only accessible to staff members.
    """
    students = db.query(User).filter(
        User.role == "student",
        User.department == department
    ).all()
    
    return {
        "department": department,
        "total_students": len(students),
        "students": [
            {
                "id": s.id,
                "name": s.name,
                "email": s.email,
                "batch": s.batch if s.batch else None
            }
            for s in students
        ]
    }

@router.post("/add-interview-feedback")
async def add_interview_feedback(
    student_id: int,
    score: int,
    feedback: str,
    interview_type: str = "general",
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db)
):
    """
    Add interview feedback for a student.
    Only staff members can add feedback.
    """
    # Check if student exists
    student = db.query(User).filter(
        User.id == student_id,
        User.role == "student"
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # Validate score
    if not (0 <= score <= 10):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Score must be between 0 and 10"
        )
    
    # Create interview report
    report = InterviewReport(
        user_id=student_id,
        score=score,
        feedback=feedback,
        interview_type=interview_type
    )
    
    db.add(report)
    db.commit()
    db.refresh(report)
    
    return {
        "message": "Feedback added successfully",
        "report_id": report.id,
        "student_name": student.name,
        "score": score
    }

@router.get("/interviews/{student_id}")
async def get_student_interviews(
    student_id: int,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db)
):
    """
    Get all interview reports for a student.
    Only accessible to staff members.
    """
    student = db.query(User).filter(User.id == student_id).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    reports = db.query(InterviewReport).filter(
        InterviewReport.user_id == student_id
    ).order_by(InterviewReport.created_at.desc()).all()
    
    return {
        "student_name": student.name,
        "email": student.email,
        "total_interviews": len(reports),
        "interviews": [
            {
                "id": r.id,
                "score": r.score,
                "feedback": r.feedback,
                "interview_type": r.interview_type,
                "created_at": r.created_at.isoformat()
            }
            for r in reports
        ]
    }

