"""
Student Dashboard Routes
"""
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Header
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel
from app.database.db import SessionLocal
from app.database.models import StudentProfile, TestAttempt, InterviewAttempt, User, Resume, Topic, Test, Interview, TestQuestion, TestAttemptDetail, test_topics_association
from app.services.vector_service import search_topic
from typing import Optional, List
from jose import JWTError, jwt
import os
from datetime import datetime

router = APIRouter(prefix="/student", tags=["student"])

# Temporary storage for selected topics for test building (user_id -> list of topic_ids)
test_builder_sessions = {}

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
            Resume.user_id == student.user_id
        ).first() is not None
        
        # Get recent test attempts (limit 5)
        recent_tests = db.query(TestAttempt).options(
            joinedload(TestAttempt.test).joinedload(Test.topics)
        ).filter(
            TestAttempt.student_id == student.id
        ).order_by(TestAttempt.created_at.desc()).limit(5).all()
        
        # Build enhanced recent test attempts data
        recent_test_attempts_data = []
        for t in recent_tests:
            # Get test questions count
            total_questions = len(t.test.questions)
            
            # Get correct answers count from test attempt details
            correct_answers = db.query(TestAttemptDetail).filter(
                TestAttemptDetail.test_attempt_id == t.id,
                TestAttemptDetail.is_correct == True
            ).count()
            
            # Get topics for this test
            topics = [topic.title for topic in t.test.topics]
            
            # Calculate percentage
            percentage = int((correct_answers / total_questions) * 100) if total_questions > 0 else 0
            
            # Determine pass/fail status
            pass_status = "pass" if percentage >= 70 else "fail"
            
            recent_test_attempts_data.append({
                "id": t.id,
                "test_id": t.test_id,
                "test_title": t.test.title,
                "score": t.score,
                "percentage": percentage,
                "status": t.status,
                "pass_status": pass_status,
                "correct_answers": correct_answers,
                "total_questions": total_questions,
                "topics": topics,
                "created_at": t.created_at.isoformat()
            })
        
        # Get recent interview attempts (limit 5)
        recent_interviews = db.query(InterviewAttempt).options(
            joinedload(InterviewAttempt.interview)
        ).filter(
            InterviewAttempt.student_id == student.id
        ).order_by(InterviewAttempt.created_at.desc()).limit(5).all()
        
        return {
            "student_name": student.name,
            "student_roll": f"{student.section}-{student.id:04d}",  # Format: A-0001
            "department": student.department.name if student.department else "Unknown",
            "metrics": {
                "total_tests_taken": test_metrics.total_attempts or 0,
                "total_interviews_taken": interview_metrics.total_attempts or 0,
                "avg_test_score": round(float(test_metrics.avg_score) if test_metrics.avg_score else 0, 2),
                "avg_interview_score": round(float(interview_metrics.avg_score) if interview_metrics.avg_score else 0, 2),
                "resume_uploaded": resume_exists
            },
            "recent_test_attempts": recent_test_attempts_data,
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
    Get available topics filtered by student's department and section
    """
    db = SessionLocal()
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="No authorization token")
        
        user_info = get_current_user(authorization)
        student_user_id = user_info["user_id"]
        
        # Get student profile with department and section
        from sqlalchemy.orm import joinedload
        student = db.query(StudentProfile).options(
            joinedload(StudentProfile.department)
        ).filter(
            StudentProfile.user_id == student_user_id
        ).first()
        
        if not student:
            raise HTTPException(status_code=404, detail="Student profile not found")
        
        # Get topics filtered by student's department and section
        topics = db.query(Topic).options(
            joinedload(Topic.staff),
            joinedload(Topic.department)
        ).filter(
            Topic.department_id == student.department_id,
            Topic.section == student.section
        ).order_by(
            Topic.created_at.desc()
        ).offset(skip).limit(limit).all()
        
        return [
            {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "staff_name": t.staff.name,
                "department_name": t.department.name if t.department else None,
                "section": t.section,
                "file_size": t.file_size,
                "is_indexed": t.is_indexed,
                "embedding_chunks": t.embedding_chunks,
                "download_url": f"/student/topics/{t.id}/download",
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
    Returns staff name from topic if test staff_name is unknown
    Includes attempt status and scores
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
            joinedload(Test.topic).joinedload(Topic.staff),
            joinedload(Test.staff),
            joinedload(Test.topics),
            joinedload(Test.questions)
        ).order_by(
            Test.created_at.desc()
        ).offset(skip).limit(limit).all()
        
        # Get student's test attempts with details (single query)
        student_attempts = db.query(TestAttempt).options(
            joinedload(TestAttempt.test)
        ).filter(
            TestAttempt.student_id == student.id
        ).all()
        
        student_test_ids = {ta.test_id for ta in student_attempts}
        attempt_details = {ta.test_id: {
            "id": ta.id,
            "score": ta.score, 
            "status": ta.status,
            "attempt_count": ta.attempt_count,
            "created_at": ta.created_at.isoformat()
        } for ta in student_attempts}
        
        result = []
        for t in tests:
            # Get staff name: prefer test.staff, fallback to primary topic staff
            staff_name = "Unknown"
            if t.staff and t.staff.name:
                staff_name = t.staff.name
            elif t.topic and t.topic.staff and t.topic.staff.name:
                staff_name = t.topic.staff.name
            
            # Get topics list
            topics_list = [topic.title for topic in t.topics] if t.topics else []
            if t.topic and t.topic.title and t.topic.title not in topics_list:
                topics_list.insert(0, t.topic.title)
            
            attempt_info = attempt_details.get(t.id, {})
            
            test_data = {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "topic_title": t.topic.title if t.topic else "General",
                "topics": topics_list,
                "staff_name": staff_name,
                "total_questions": len(t.questions) if t.questions else 0,
                "attempted": t.id in student_test_ids,
                "attempt_id": attempt_info.get("id"),
                "attempt_score": attempt_info.get("score"),
                "attempt_status": attempt_info.get("status"),
                "attempt_count": attempt_info.get("attempt_count", 0),
                "attempted_at": attempt_info.get("created_at"),
                "created_at": t.created_at.isoformat()
            }
            
            # Add pass/fail status if attempted
            if t.id in student_test_ids and attempt_info.get("score") is not None:
                test_data["pass_status"] = "pass" if attempt_info.get("score") >= 70 else "fail"
            
            result.append(test_data)
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching tests: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/topics/{topic_id}/tests")
async def get_topic_tests(
    topic_id: int,
    authorization: Optional[str] = Header(None)
):
    """
    Get all tests created from a specific topic, with attempt status and details
    Returns detailed information about each test and attempt
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
        
        # Verify topic exists
        topic = db.query(Topic).options(
            joinedload(Topic.staff)
        ).filter(Topic.id == topic_id).first()
        
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")
        
        # Get tests created from this topic (check via test.topics relationship)
        tests = db.query(Test).options(
            joinedload(Test.questions)
        ).filter(
            Test.topics.any(Topic.id == topic_id)
        ).order_by(Test.created_at.desc()).all()
        
        # If no tests found via topics relationship, try single topic
        if not tests:
            tests = db.query(Test).options(
                joinedload(Test.questions)
            ).filter(Test.topic_id == topic_id).order_by(Test.created_at.desc()).all()
        
        # Get student's test attempts with details
        student_attempts = db.query(TestAttempt).options(
            joinedload(TestAttempt.test)
        ).filter(
            TestAttempt.student_id == student.id,
            TestAttempt.test_id.in_([t.id for t in tests])
        ).all() if tests else []
        
        attempt_map = {ta.test_id: ta for ta in student_attempts}
        
        result = []
        for t in tests:
            attempt = attempt_map.get(t.id)
            
            test_data = {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "total_questions": len(t.questions),
                "attempted": attempt is not None,
                "attempt_id": attempt.id if attempt else None,
                "attempt_score": attempt.score if attempt else None,
                "attempt_status": attempt.status if attempt else None,
                "attempt_count": attempt.attempt_count if attempt else 0,
                "attempted_at": attempt.created_at.isoformat() if attempt else None,
                "created_at": t.created_at.isoformat()
            }
            
            # Add calculated fields
            if attempt:
                # Get answer statistics
                correct_count = db.query(TestAttemptDetail).filter(
                    TestAttemptDetail.test_attempt_id == attempt.id,
                    TestAttemptDetail.is_correct == True
                ).count()
                test_data["correct_answers"] = correct_count
                test_data["incorrect_answers"] = len(t.questions) - correct_count
                test_data["pass_status"] = "pass" if attempt.score >= 70 else "fail"
            
            result.append(test_data)
        
        return {
            "topic_id": topic_id,
            "topic_title": topic.title,
            "staff_name": topic.staff.name if topic.staff else "Unknown",
            "tests": result,
            "total_tests": len(result),
            "attempted_tests": len([t for t in result if t["attempted"]]),
            "pending_tests": len([t for t in result if not t["attempted"]]),
            "summary": {
                "total_created": len(result),
                "total_attempted": len([t for t in result if t["attempted"]]),
                "total_pending": len([t for t in result if not t["attempted"]]),
                "average_score": round(sum([t["attempt_score"] for t in result if t["attempt_score"]]) / len([t for t in result if t["attempt_score"]]), 2) if [t for t in result if t["attempt_score"]] else 0
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching topic tests: {e}")
        import traceback
        traceback.print_exc()
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
                "staff_name": i.staff.name if i.staff else "Unknown",
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
            Resume.user_id == student.user_id
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
            user_id=student.user_id,
            file_path=file_path
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
            Resume.user_id == student.user_id
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


@router.get("/topics/{topic_id}/download")
async def download_topic_pdf(
    topic_id: int,
    authorization: Optional[str] = Header(None)
):
    """
    Download topic PDF file (only if student's department and section match)
    """
    db = SessionLocal()
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="No authorization token")
        
        user_info = get_current_user(authorization)
        student_user_id = user_info["user_id"]
        
        # Get student profile
        from sqlalchemy.orm import joinedload
        student = db.query(StudentProfile).options(
            joinedload(StudentProfile.department)
        ).filter(
            StudentProfile.user_id == student_user_id
        ).first()
        
        if not student:
            raise HTTPException(status_code=404, detail="Student profile not found")
        
        # Verify topic exists and belongs to student's department and section
        topic = db.query(Topic).filter(Topic.id == topic_id).first()
        
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")
        
        # Verify student has access to this topic
        if topic.department_id != student.department_id or topic.section != student.section:
            raise HTTPException(status_code=403, detail="You don't have access to this topic")
        
        if not os.path.exists(topic.file_path):
            raise HTTPException(status_code=404, detail="PDF file not found")
        
        from fastapi.responses import FileResponse
        
        # Return the file with proper headers for download
        return FileResponse(
            topic.file_path,
            media_type="application/pdf",
            filename=f"{topic.title}.pdf"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/test-attempt/{attempt_id}/details")
async def get_test_attempt_details(
    attempt_id: int,
    authorization: Optional[str] = Header(None)
):
    """
    Get detailed results for a test attempt
    Returns: total_questions, correct_count, wrong_count, score, status (pass/fail)
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
        
        # Get the test attempt
        attempt = db.query(TestAttempt).filter(
            TestAttempt.id == attempt_id,
            TestAttempt.student_id == student.id
        ).first()
        
        if not attempt:
            raise HTTPException(status_code=404, detail="Test attempt not found")
        
        # Get the test
        test = db.query(Test).filter(Test.id == attempt.test_id).first()
        
        if not test:
            raise HTTPException(status_code=404, detail="Test not found")
        
        # Count total questions
        total_questions = db.query(TestQuestion).filter(
            TestQuestion.test_id == test.id
        ).count()
        
        # Count correct answers
        correct_count = db.query(TestAttemptDetail).filter(
            TestAttemptDetail.test_attempt_id == attempt.id,
            TestAttemptDetail.is_correct == True
        ).count()
        
        # Calculate wrong answers
        wrong_count = total_questions - correct_count
        
        # Determine pass/fail (assuming 70% is passing)
        score = attempt.score or 0
        status = "pass" if score >= 70 else "fail"
        
        return {
            "attempt_id": attempt.id,
            "test_id": test.id,
            "test_title": test.title,
            "total_questions": total_questions,
            "correct_count": correct_count,
            "wrong_count": wrong_count,
            "score": score,
            "status": status,
            "attempted_at": attempt.created_at.isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching test attempt details: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
