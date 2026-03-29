"""
Test Builder Routes - Student-generated tests from topics
"""
from fastapi import APIRouter, HTTPException, Header
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel
from app.database.db import SessionLocal
from app.database.models import StudentProfile, Topic, Test, TestQuestion, test_topics_association
from app.services.gemini_service import generate_mcq_questions
from typing import Optional, List
from jose import JWTError, jwt
import os
from datetime import datetime

router = APIRouter(prefix="/student/test-builder", tags=["test-builder"])

SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
ALGORITHM = "HS256"

# Temporary storage for selected topics (user_id -> {topics, mcqs})
test_builder_sessions = {}


class MCQQuestion(BaseModel):
    question: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_option: str  # A, B, C, D
    explanation: Optional[str] = None


class GenerateMCQRequest(BaseModel):
    topic_ids: List[int]
    num_questions: int = 5


def get_current_user(token: str = None) -> dict:
    """Extract user info from JWT token"""
    if not token:
        raise HTTPException(status_code=401, detail="No token provided")
    
    try:
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


@router.get("/selected-topics")
async def get_selected_topics(authorization: Optional[str] = Header(None)):
    """Get topics currently selected for test building"""
    user_info = get_current_user(authorization)
    user_id = user_info["user_id"]
    
    session_data = test_builder_sessions.get(user_id, {})
    selected_topics = session_data.get("topics", [])
    
    db = SessionLocal()
    try:
        topics = db.query(Topic).filter(Topic.id.in_(selected_topics)).all()
        
        return {
            "selected_topics": [
                {
                    "id": t.id,
                    "title": t.title,
                    "description": t.description,
                    "staff_name": t.staff.name
                }
                for t in topics
            ],
            "count": len(topics)
        }
    finally:
        db.close()


@router.post("/add-topic/{topic_id}")
async def add_topic_to_test(topic_id: int, authorization: Optional[str] = Header(None)):
    """Add a topic to test builder (only if student has access)"""
    user_info = get_current_user(authorization)
    user_id = user_info["user_id"]
    
    db = SessionLocal()
    try:
        # Get student profile
        from sqlalchemy.orm import joinedload
        student = db.query(StudentProfile).options(
            joinedload(StudentProfile.department)
        ).filter(
            StudentProfile.user_id == user_id
        ).first()
        
        if not student:
            raise HTTPException(status_code=404, detail="Student profile not found")
        
        # Verify topic exists
        topic = db.query(Topic).filter(Topic.id == topic_id).first()
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")
        
        # Verify student has access to this topic
        if topic.department_id != student.department_id or topic.section != student.section:
            raise HTTPException(status_code=403, detail="You don't have access to this topic")
        
        # Add to session
        if user_id not in test_builder_sessions:
            test_builder_sessions[user_id] = {"topics": [], "mcqs": []}
        
        if topic_id not in test_builder_sessions[user_id]["topics"]:
            test_builder_sessions[user_id]["topics"].append(topic_id)
        
        return {
            "message": f"Added '{topic.title}' to test",
            "selected_count": len(test_builder_sessions[user_id]["topics"])
        }
    finally:
        db.close()


@router.post("/remove-topic/{topic_id}")
async def remove_topic_from_test(topic_id: int, authorization: Optional[str] = Header(None)):
    """Remove a topic from test builder"""
    user_info = get_current_user(authorization)
    user_id = user_info["user_id"]
    
    if user_id in test_builder_sessions and topic_id in test_builder_sessions[user_id]["topics"]:
        test_builder_sessions[user_id]["topics"].remove(topic_id)
    
    return {
        "message": "Topic removed",
        "selected_count": len(test_builder_sessions.get(user_id, {}).get("topics", []))
    }


@router.post("/generate-mcqs")
async def generate_mcqs(request: GenerateMCQRequest, authorization: Optional[str] = Header(None)):
    """Generate MCQ questions from selected topics"""
    user_info = get_current_user(authorization)
    user_id = user_info["user_id"]
    
    db = SessionLocal()
    try:
        session_data = test_builder_sessions.get(user_id, {})
        selected_topics = session_data.get("topics", [])
        
        if not selected_topics:
            raise HTTPException(status_code=400, detail="No topics selected")
        
        # Get topic content for MCQ generation
        topics = db.query(Topic).filter(Topic.id.in_(selected_topics)).all()
        
        # Generate MCQs using Gemini service
        from app.services.vector_service import search_topic
        
        mcqs = []
        for topic in topics:
            try:
                # Search for key content from each topic
                results = search_topic(topic.id, f"important concepts in {topic.title}", k=3)
                
                # Generate MCQs - use search results if available, otherwise use topic title
                if results:
                    content = " ".join([r.get("content", "") for r in results])
                else:
                    content = topic.title  # Fallback to topic title if no search results
                
                generated_mcqs = generate_mcq_questions(content, topic.title, request.num_questions)
                if generated_mcqs:
                    mcqs.extend(generated_mcqs)
                else:
                    # If MCQ generation fails, create placeholder
                    mcqs.append({
                        "question": f"Sample question from {topic.title}",
                        "option_a": "Option A",
                        "option_b": "Option B",
                        "option_c": "Option C",
                        "option_d": "Option D",
                        "correct_option": "A",
                        "explanation": f"Explanation for {topic.title}"
                    })
            except Exception as e:
                # If any error occurs, create placeholder MCQ
                print(f"Error generating MCQs for {topic.title}: {e}")
                mcqs.append({
                    "question": f"Sample question from {topic.title}",
                    "option_a": "Option A",
                    "option_b": "Option B",
                    "option_c": "Option C",
                    "option_d": "Option D",
                    "correct_option": "A",
                    "explanation": f"Explanation for {topic.title}"
                })
        
        # Store MCQs in session
        test_builder_sessions[user_id]["mcqs"] = mcqs
        
        return {
            "mcqs": mcqs,
            "total_questions": len(mcqs),
            "topics_count": len(selected_topics)
        }
    finally:
        db.close()


@router.post("/create-test")
async def create_test(
    title: Optional[str] = None,
    authorization: Optional[str] = Header(None)
):
    """Create a test from generated MCQs"""
    user_info = get_current_user(authorization)
    user_id = user_info["user_id"]
    
    db = SessionLocal()
    try:
        # Get student profile
        student = db.query(StudentProfile).filter(
            StudentProfile.user_id == user_id
        ).first()
        
        if not student:
            raise HTTPException(status_code=404, detail="Student profile not found")
        
        session_data = test_builder_sessions.get(user_id, {})
        selected_topics = session_data.get("topics", [])
        mcqs = session_data.get("mcqs", [])
        
        if not selected_topics or not mcqs:
            raise HTTPException(status_code=400, detail="Please generate MCQs first")
        
        # Create test with title: topic name + timestamp
        topics = db.query(Topic).filter(Topic.id.in_(selected_topics)).all()
        topic_names = " + ".join([t.title for t in topics])
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        test_title = title or f"{topic_names} - {timestamp}"
        
        # Create test
        new_test = Test(
            title=test_title,
            description=f"Student-created test from {len(selected_topics)} topic(s)",
            created_by_student_id=student.id
        )
        
        # Add topics to test
        new_test.topics = topics
        
        db.add(new_test)
        db.flush()  # Get test ID without committing
        
        # Add questions to test
        for i, mcq_data in enumerate(mcqs):
            question = TestQuestion(
                test_id=new_test.id,
                question_text=mcq_data.get("question", ""),
                option_a=mcq_data.get("option_a", ""),
                option_b=mcq_data.get("option_b", ""),
                option_c=mcq_data.get("option_c", ""),
                option_d=mcq_data.get("option_d", ""),
                correct_option=mcq_data.get("correct_option", "A"),
                explanation=mcq_data.get("explanation", ""),
                topic_id=selected_topics[i % len(selected_topics)]  # Distribute questions among topics
            )
            db.add(question)
        
        db.commit()
        
        # Clear session
        if user_id in test_builder_sessions:
            del test_builder_sessions[user_id]
        
        return {
            "message": "Test created successfully",
            "test_id": new_test.id,
            "test_title": new_test.title,
            "total_questions": len(mcqs),
            "topics_count": len(selected_topics)
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/tests/{test_id}")
async def get_test_questions(
    test_id: int,
    authorization: Optional[str] = Header(None)
):
    """Get test questions for a specific test"""
    user_info = get_current_user(authorization)
    user_id = user_info["user_id"]
    
    db = SessionLocal()
    try:
        # Get student profile
        student = db.query(StudentProfile).filter(
            StudentProfile.user_id == user_id
        ).first()
        
        if not student:
            raise HTTPException(status_code=404, detail="Student profile not found")
        
        # Get test with questions
        test = db.query(Test).options(
            joinedload(Test.questions)
        ).filter(Test.id == test_id).first()
        
        if not test:
            raise HTTPException(status_code=404, detail="Test not found")
        
        # Return test details with questions
        return {
            "id": test.id,
            "title": test.title,
            "description": test.description,
            "total_questions": len(test.questions),
            "created_at": test.created_at.isoformat(),
            "questions": [
                {
                    "id": q.id,
                    "question_text": q.question_text,
                    "option_a": q.option_a,
                    "option_b": q.option_b,
                    "option_c": q.option_c,
                    "option_d": q.option_d,
                    "correct_option": q.correct_option,
                    "explanation": q.explanation
                }
                for q in test.questions
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
