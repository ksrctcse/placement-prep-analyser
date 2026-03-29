"""
Student Dashboard Routes
"""
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database.db import SessionLocal
from app.database.models import StudentProfile, TestAttempt, InterviewAttempt, User, Resume, Topic, Test, Interview
from app.services.vector_service import search_topic
from typing import Optional
from jose import JWTError, jwt
import os

router = APIRouter(prefix="/student", tags=["student"])

# Configuration
UPLOAD_DIR = "uploads/resumes"
MAX_RESUME_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_RESUME_TYPES = {"pdf", "doc", "docx"}
SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
ALGORITHM = "HS256"


# Helper function to get current user from token
def get_current_user(token: str = None) -> dict:
    """Extract user info from JWT token"""
    if not token:
        raise HTTPException(status_code=401, detail="No token provided")
    
    try:
        # Extract token from Bearer scheme if present
        if token.startswith("Bearer "):
            token = token[7:]
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        role = payload.get("role")
        
        if not user_id or role != "student":
            raise HTTPException(status_code=403, detail="Not authorized")
        
        return {"user_id": user_id, "role": role}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.get("/dashboard")
async def get_student_dashboard(authorization: Optional[str] = Header(None)):
    """
    Get student dashboard with metrics (optimized)
    """
    db = SessionLocal()
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="No authorization token")
        
        user_info = get_current_user(authorization)
        student_user_id = user_info["user_id"]
        
        # Get student profile with eager loading
        from sqlalchemy.orm import joinedload
        student = db.query(StudentProfile).options(
            joinedload(StudentProfile.department)
        ).filter(
            StudentProfile.user_id == student_user_id
        ).first()
        
        if not student:
            raise HTTPException(status_code=404, detail="Student profile not found")
        
        # Get metrics using database aggregations
        from sqlalchemy import func
        
        test_metrics = db.query(
            func.count(TestAttempt.id).label('total_attempts'),
            func.avg(TestAttempt.score).label('avg_score')
        ).filter(
            TestAttempt.student_id == student.id
        ).first()
        
        interview_metrics = db.query(
            func.count(InterviewAttempt.id).label('total_attempts'),
            func.avg(InterviewAttempt.score).label('avg_score')
        ).filter(
            InterviewAttempt.student_id == student.id
        ).first()
        
        # Get resume info
        resume_exists = db.query(Resume).filter(
            Resume.student_id == student.id
        ).first() is not None
        
        # Get recent test attempts (limit 5)
        recent_tests = db.query(TestAttempt).options(
            joinedload(TestAttempt.test)
        ).filter(
            TestAttempt.student_id == student.id
        ).order_by(TestAttempt.created_at.desc()).limit(5).all()
        
        # Get recent interview attempts (limit 5)
        recent_interviews = db.query(InterviewAttempt).options(
            joinedload(InterviewAttempt.interview)
        ).filter(
            InterviewAttempt.student_id == student.id
        ).order_by(InterviewAttempt.created_at.desc()).limit(5).all()
        
        return {
            "student_name": student.name,
            "student_roll": getattr(student, 'roll_number', 'N/A'),
            "department": student.department.name,
            "metrics": {
                "total_tests_taken": test_metrics.total_attempts or 0,
                "total_interviews_taken": interview_metrics.total_attempts or 0,
                "avg_test_score": round(float(test_metrics.avg_score) if test_metrics.avg_score else 0, 2),
                "avg_interview_score": round(float(interview_metrics.avg_score) if interview_metrics.avg_score else 0, 2),
                "resume_uploaded": resume_exists
            },
            "recent_test_attempts": [
                {
                    "id": t.id,
                    "test_title": t.test.title,
                    "score": t.score,
                    "status": t.status,
                    "created_at": t.created_at.isoformat()
                }
                for t in recent_tests
            ],
            "recent_interview_attempts": [
                {
                    "id": i.id,
                    "interview_title": i.interview.title,
                    "score": i.score,
                    "status": i.status,
                    "created_at": i.created_at.isoformat()
                }
                for i in recent_interviews
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/topics")
async def get_topics(
    authorization: Optional[str] = Header(None),
    skip: int = 0,
    limit: int = 20
):
    """
    Get all available topics (with pagination)
    """
    db = SessionLocal()
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="No authorization token")
        
        user_info = get_current_user(authorization)
        
        # Paginated query with eager loading
        from sqlalchemy.orm import joinedload
        topics = db.query(Topic).options(
            joinedload(Topic.staff)
        ).order_by(
            Topic.created_at.desc()
        ).offset(skip).limit(limit).all()
        
        return [
            {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "staff_name": t.staff.name,
                "created_at": t.created_at.isoformat()
            }
            for t in topics
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/tests")
async def get_tests(
    authorization: Optional[str] = Header(None),
    skip: int = 0,
    limit: int = 20
):
    """
    Get all available tests from topics (with pagination)
    """
    db = SessionLocal()
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="No authorization token")
        
        user_info = get_current_user(authorization)
        student_user_id = user_info["user_id"]
        
        student = db.query(StudentProfile).filter(
            StudentProfile.user_id == student_user_id
        ).first()
        
        if not student:
            raise HTTPException(status_code=404, detail="Student profile not found")
        
        # Get paginated tests with eager loading
        from sqlalchemy.orm import joinedload
        tests = db.query(Test).options(
            joinedload(Test.topic),
            joinedload(Test.staff)
        ).order_by(
            Test.created_at.desc()
        ).offset(skip).limit(limit).all()
        
        # Get student's test attempts (single query)
        student_test_ids = {t.test_id for t in db.query(TestAttempt.test_id).filter(
            TestAttempt.student_id == student.id
        ).all()}
        
        return [
            {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "topic_title": t.topic.title if t.topic else "General",
                "staff_name": t.staff.name,
                "attempted": t.id in student_test_ids,
                "created_at": t.created_at.isoformat()
            }
            for t in tests
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/interviews")
async def get_interviews(
    authorization: Optional[str] = Header(None),
    skip: int = 0,
    limit: int = 20
):
    """
    Get all available interviews (with pagination)
    """
    db = SessionLocal()
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="No authorization token")
        
        user_info = get_current_user(authorization)
        student_user_id = user_info["user_id"]
        
        student = db.query(StudentProfile).filter(
            StudentProfile.user_id == student_user_id
        ).first()
        
        if not student:
            raise HTTPException(status_code=404, detail="Student profile not found")
        
        # Get paginated interviews with eager loading
        from sqlalchemy.orm import joinedload
        interviews = db.query(Interview).options(
            joinedload(Interview.topic),
            joinedload(Interview.staff)
        ).order_by(
            Interview.created_at.desc()
        ).offset(skip).limit(limit).all()
        
        # Get student's interview attempts (single query)
        student_interview_ids = {i.interview_id for i in db.query(InterviewAttempt.interview_id).filter(
            InterviewAttempt.student_id == student.id
        ).all()}
        
        return [
            {
                "id": i.id,
                "title": i.title,
                "description": i.description,
                "topic_title": i.topic.title if i.topic else "General",
                "staff_name": i.staff.name,
                "attempted": i.id in student_interview_ids,
                "created_at": i.created_at.isoformat()
            }
            for i in interviews
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/upload-resume")
async def upload_resume(
    file: UploadFile = File(...),
    authorization: Optional[str] = Header(None)
):
    """
    Upload student resume (PDF/DOC/DOCX, max 10MB)
    """
    db = SessionLocal()
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="No authorization token")
        
        user_info = get_current_user(authorization)
        student_user_id = user_info["user_id"]
        
        # Get student profile
        student = db.query(StudentProfile).filter(
            StudentProfile.user_id == student_user_id
        ).first()
        
        if not student:
            raise HTTPException(status_code=404, detail="Student profile not found")
        
        # Validate file extension
        file_ext = file.filename.split(".")[-1].lower()
        if file_ext not in ALLOWED_RESUME_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_RESUME_TYPES)}"
            )
        
        # Read file content to check size
        content = await file.read()
        file_size = len(content)
        
        if file_size > MAX_RESUME_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File size exceeds 10MB limit. Current size: {file_size / 1024 / 1024:.2f}MB"
            )
        
        # Create upload directory if it doesn't exist
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        
        # Check if student already has a resume and delete old one
        existing_resume = db.query(Resume).filter(
            Resume.student_id == student.id
        ).first()
        
        if existing_resume:
            try:
                os.remove(existing_resume.file_path)
            except:
                pass
            db.delete(existing_resume)
        
        # Save file
        from datetime import datetime
        file_path = os.path.join(UPLOAD_DIR, f"{student.id}_{datetime.now().timestamp()}_{file.filename}")
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Create or update resume record
        resume = Resume(
            student_id=student.id,
            file_path=file_path,
            file_size=file_size
        )
        db.add(resume)
        db.commit()
        db.refresh(resume)
        
        return {
            "id": resume.id,
            "file_name": file.filename,
            "file_size": file_size,
            "uploaded_at": resume.created_at.isoformat(),
            "message": "Resume uploaded successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/resume")
async def get_resume(authorization: Optional[str] = Header(None)):
    """
    Get student's resume info
    """
    db = SessionLocal()
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="No authorization token")
        
        user_info = get_current_user(authorization)
        student_user_id = user_info["user_id"]
        
        student = db.query(StudentProfile).filter(
            StudentProfile.user_id == student_user_id
        ).first()
        
        if not student:
            raise HTTPException(status_code=404, detail="Student profile not found")
        
        resume = db.query(Resume).filter(
            Resume.student_id == student.id
        ).first()
        
        if not resume:
            return {"resume": None, "message": "No resume uploaded yet"}
        
        return {
            "id": resume.id,
            "file_path": resume.file_path,
            "file_size": resume.file_size,
            "uploaded_at": resume.created_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/search-topic/{topic_id}")
async def search_topic_for_student(
    topic_id: int,
    query: str,
    authorization: Optional[str] = Header(None)
):
    """
    Search within a topic using RAG/semantic similarity
    Students can search within topics to find relevant content
    """
    db = SessionLocal()
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="No authorization token")
        
        user_info = get_current_user(authorization)
        
        # Get topic
        topic = db.query(Topic).filter(Topic.id == topic_id).first()
        
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")
        
        if not topic.is_indexed:
            raise HTTPException(
                status_code=400,
                detail="This topic has not been indexed for semantic search yet. Please try again later."
            )
        
        if not query or not query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Perform semantic search within the topic
        results = search_topic(topic_id, query, k=5)
        
        return {
            "topic_id": topic_id,
            "topic_title": topic.title,
            "query": query,
            "results": results,
            "num_results": len(results)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
