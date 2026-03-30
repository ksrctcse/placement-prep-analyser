"""
Test Builder Routes - Student-generated tests from topics
"""
from fastapi import APIRouter, HTTPException, Header
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel
from app.database.db import SessionLocal
from app.database.models import (
    StudentProfile, Topic, Test, TestQuestion, TestAttempt, TestAttemptDetail,
    TestAnalysis, TopicPerformance, test_topics_association
)
from app.services.gemini_service import generate_mcq_questions
from app.services.mcq_agent import generate_mcqs_from_topics, store_mcqs_in_database
from app.services.analysis_agent import analyze_test_performance, get_test_analysis
from typing import Optional, List, Dict
from jose import JWTError, jwt
import os
import json
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
    topic_ids: Optional[List[int]] = None  # Optional: uses session-selected topics if not provided
    num_questions: int = 10  # Default 10, max enforced at 10


class TestAnswerRequest(BaseModel):
    test_id: int
    answers: Dict[int, str]  # question_id -> student_answer (A, B, C, D)


class SubmitTestRequest(BaseModel):
    test_id: int
    answers: Dict[int, str]  # question_id -> student_answer (A, B, C, D)
    time_taken: Optional[int] = None  # in seconds


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
async def generate_mcqs(request: Optional[GenerateMCQRequest] = None, authorization: Optional[str] = Header(None)):
    """
    Generate maximum 10 MCQ questions from student's selected topics.
    Uses topics already selected via /add-topic endpoints.
    Optional: can override with topic_ids in request body if needed.
    
    Flow:
    1. Student selects topics via POST /add-topic/{topic_id}
    2. Student calls POST /generate-mcqs (uses selected topics by default)
    3. Or optionally POST /generate-mcqs with custom topic_ids in body
    """
    user_info = get_current_user(authorization)
    user_id = user_info["user_id"]
    
    # Default request if not provided
    if not request:
        request = GenerateMCQRequest()
    
    db = SessionLocal()
    try:
        # Get student profile
        student = db.query(StudentProfile).filter(
            StudentProfile.user_id == user_id
        ).first()
        
        if not student:
            raise HTTPException(status_code=404, detail="Student profile not found")
        
        # Get selected topics from session
        session_data = test_builder_sessions.get(user_id, {})
        session_topics = session_data.get("topics", [])
        
        # Use topic_ids from request if provided, otherwise use session topics
        if request.topic_ids:
            # Use provided topic_ids (for flexibility) and update session
            topic_ids = request.topic_ids
            if user_id not in test_builder_sessions:
                test_builder_sessions[user_id] = {"topics": [], "mcqs": []}
            test_builder_sessions[user_id]["topics"] = topic_ids
            print(f"\n📌 Using provided topic_ids: {topic_ids}")
        else:
            # Use student's selected topics from session (default workflow)
            if not session_topics:
                raise HTTPException(
                    status_code=400,
                    detail="❌ No topics selected. Please add topics using POST /add-topic/{topic_id} first or provide topic_ids in request body."
                )
            topic_ids = session_topics
            print(f"\n📌 Using selected topics from session: {topic_ids}")
        
        print(f"📚 Generating MCQs from {len(topic_ids)} selected topic(s)")
        print(f"   Topic IDs: {topic_ids}")
        print(f"   Student: ID {student.id}")
        
        # Generate MCQs using the AI agent
        # Always generate minimum 10 MCQs from indexed PDFs
        result = generate_mcqs_from_topics(
            db=db,
            topic_ids=topic_ids,
            student_id=student.id,
            num_questions=10,  # Always request 10 questions
            min_questions=10,  # Minimum 10 MCQs from indexed PDFs
            max_questions=10   # Enforced maximum of 10 questions
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Store MCQs in session for next step (create-test)
        if user_id not in test_builder_sessions:
            test_builder_sessions[user_id] = {"topics": [], "mcqs": []}
        
        test_builder_sessions[user_id]["topics"] = topic_ids
        test_builder_sessions[user_id]["mcqs"] = result["mcqs"]
        
        return {
            "success": True,
            "mcqs": result["mcqs"],
            "total_questions": result["total_questions"],
            "topics_count": result["topics_count"],
            "department": result.get("department", "Unknown"),
            "section": result.get("section", "Unknown"),
            "message": f"Generated {result['total_questions']} questions from {result['topics_count']} topic(s)"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in MCQ generation: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating MCQs: {str(e)}")
    finally:
        db.close()


@router.post("/create-test")
async def create_test(
    title: Optional[str] = None,
    authorization: Optional[str] = Header(None)
):
    """
    Create a test from generated MCQs with proper student-topic mapping.
    Stores all questions, answers, and correct answers in database.
    """
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
        
        # Verify MCQ count doesn't exceed 10
        if len(mcqs) > 10:
            mcqs = mcqs[:10]  # Enforce maximum 10 questions
            print(f"⚠️  MCQ count exceeded 10, truncated to {len(mcqs)}")
        
        # Create test with title: topic name + timestamp
        topics = db.query(Topic).filter(Topic.id.in_(selected_topics)).all()
        topic_names = " + ".join([t.title for t in topics])
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        test_title = title or f"{topic_names} - {timestamp}"
        
        print(f"\n📝 Creating Test with {len(mcqs)} questions")
        print(f"   Title: {test_title}")
        print(f"   Topics: {len(selected_topics)}")
        print(f"   Student: ID {student.id}")
        
        # Create test
        new_test = Test(
            title=test_title,
            description=f"Student-created test from {len(selected_topics)} topic(s) with {len(mcqs)} questions",
            created_by_student_id=student.id
        )
        
        # Add topics to test
        new_test.topics = topics
        
        db.add(new_test)
        db.flush()  # Get test ID without committing
        
        test_id = new_test.id
        
        # Store MCQs with proper student-topic mapping
        storage_result = store_mcqs_in_database(
            db=db,
            test_id=test_id,
            mcqs=mcqs,
            topic_ids=selected_topics,
            student_id=student.id
        )
        
        if not storage_result.get("success"):
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to store questions: {storage_result.get('error', 'Unknown error')}"
            )
        
        # Final commit
        db.commit()
        
        # Clear session
        if user_id in test_builder_sessions:
            del test_builder_sessions[user_id]
        
        print(f"\n✅ Test created and stored successfully")
        
        return {
            "success": True,
            "message": "Test created and stored successfully with student-topic mapping",
            "test_id": test_id,
            "test_title": test_title,
            "total_questions": len(mcqs),
            "topics_count": len(selected_topics),
            "student_id": student.id,
            "topic_ids": selected_topics,
            "stored_questions": storage_result.get("stored_count", 0),
            "created_at": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating test: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error creating test: {str(e)}")
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


@router.post("/submit-test")
async def submit_test(
    request: SubmitTestRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Submit test answers and get analysis results.
    Records all answers, calculates score, and triggers AI analysis.
    """
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
        ).filter(Test.id == request.test_id).first()
        
        if not test:
            raise HTTPException(status_code=404, detail="Test not found")
        
        # Calculate score
        total_questions = len(test.questions)
        correct_answers = 0
        
        # Create TestAttempt record
        test_attempt = TestAttempt(
            test_id=request.test_id,
            student_id=student.id,
            status="completed"
        )
        
        db.add(test_attempt)
        db.flush()  # Get the ID without committing
        
        # Process each answer
        for question in test.questions:
            student_answer = request.answers.get(str(question.id))
            is_correct = student_answer == question.correct_option
            
            if is_correct:
                correct_answers += 1
            
            # Record answer details
            answer_detail = TestAttemptDetail(
                test_attempt_id=test_attempt.id,
                question_id=question.id,
                topic_id=question.topic_id,
                student_answer=student_answer,
                correct_answer=question.correct_option,
                is_correct=is_correct,
                time_spent=0  # Can be enhanced to track per-question time
            )
            
            db.add(answer_detail)
        
        # Calculate score percentage
        score = int((correct_answers / total_questions) * 100) if total_questions > 0 else 0
        test_attempt.score = score
        
        db.commit()
        
        # Trigger AI analysis
        analysis_result = analyze_test_performance(db, test_attempt.id)
        
        return {
            "success": True,
            "test_attempt_id": test_attempt.id,
            "test_id": request.test_id,
            "total_questions": total_questions,
            "correct_answers": correct_answers,
            "incorrect_answers": total_questions - correct_answers,
            "overall_percentage": score,
            "pass_status": score >= 70,
            "analysis": {
                "strengths": analysis_result.get("strengths", []),
                "weaknesses": analysis_result.get("weaknesses", []),
                "recommendations": analysis_result.get("recommendations", []),
                "topic_wise_performance": analysis_result.get("topic_wise_performance", {}),
                "message": analysis_result.get("score_message", "Test completed")
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error submitting test: {e}")
        raise HTTPException(status_code=500, detail=f"Error submitting test: {str(e)}")
    finally:
        db.close()


@router.get("/test-analysis/{test_attempt_id}")
async def get_test_analysis_details(
    test_attempt_id: int,
    authorization: Optional[str] = Header(None)
):
    """Get detailed analysis for a completed test attempt"""
    user_info = get_current_user(authorization)
    user_id = user_info["user_id"]
    
    db = SessionLocal()
    try:
        # Verify student owns this attempt
        student = db.query(StudentProfile).filter(
            StudentProfile.user_id == user_id
        ).first()
        
        if not student:
            raise HTTPException(status_code=404, detail="Student profile not found")
        
        test_attempt = db.query(TestAttempt).filter(
            TestAttempt.id == test_attempt_id,
            TestAttempt.student_id == student.id
        ).first()
        
        if not test_attempt:
            raise HTTPException(status_code=404, detail="Test attempt not found")
        
        # Get analysis
        analysis = get_test_analysis(db, test_attempt_id)
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        return {
            "success": True,
            "analysis": analysis
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/student-test-history")
async def get_student_test_history(
    authorization: Optional[str] = Header(None)
):
    """Get test history and results for the logged-in student"""
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
        
        # Get all test attempts for this student
        test_attempts = db.query(TestAttempt).filter(
            TestAttempt.student_id == student.id
        ).order_by(TestAttempt.created_at.desc()).all()
        
        test_history = []
        for attempt in test_attempts:
            test = db.query(Test).filter(Test.id == attempt.test_id).first()
            analysis = db.query(TestAnalysis).filter(
                TestAnalysis.test_attempt_id == attempt.id
            ).first()
            
            test_history.append({
                "test_attempt_id": attempt.id,
                "test_id": attempt.test_id,
                "test_title": test.title if test else "Unknown Test",
                "score": attempt.score,
                "status": attempt.status,
                "attempted_at": attempt.created_at.isoformat(),
                "pass_status": attempt.score >= 70 if attempt.score else False,
                "has_analysis": analysis is not None
            })
        
        return {
            "success": True,
            "student_name": student.name,
            "department": student.department.name if student.department else "Unknown",
            "section": student.section,
            "total_tests_attempted": len(test_attempts),
            "test_history": test_history
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/topic-performance-summary")
async def get_topic_performance_summary(
    authorization: Optional[str] = Header(None)
):
    """Get performance summary across all topics for the student"""
    from sqlalchemy.orm import joinedload
    
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
        
        # Get topic performance for this student
        topic_performances = db.query(TopicPerformance).options(
            joinedload(TopicPerformance.topic)
        ).filter(
            TopicPerformance.student_id == student.id
        ).order_by(TopicPerformance.average_percentage.asc()).all()
        
        # Aggregate statistics
        total_topics_attempted = len(topic_performances)
        mastered_topics = sum(1 for tp in topic_performances if tp.mastery_status)
        avg_percentage = int(sum(tp.average_percentage for tp in topic_performances) / total_topics_attempted) if total_topics_attempted > 0 else 0
        
        topic_details = []
        for tp in topic_performances:
            topic_details.append({
                "topic_id": tp.topic_id,
                "topic_name": tp.topic.title if tp.topic else "Unknown",
                "average_percentage": tp.average_percentage,
                "last_attempt_percentage": tp.last_attempt_percentage,
                "proficiency_level": tp.proficiency_level,
                "mastery_status": tp.mastery_status,
                "total_attempts": tp.total_attempts,
                "last_attempted_at": tp.last_attempted_at.isoformat() if tp.last_attempted_at else None
            })
        
        return {
            "success": True,
            "student_name": student.name,
            "total_topics_attempted": total_topics_attempted,
            "mastered_topics": mastered_topics,
            "overall_average_percentage": avg_percentage,
            "topic_details": topic_details
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/recent-test-results")
async def get_recent_test_results(
    limit: int = 5,
    authorization: Optional[str] = Header(None)
):
    """Get recent test results for the student with analysis"""
    from sqlalchemy.orm import joinedload
    
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
        
        # Get recent test attempts
        test_attempts = db.query(TestAttempt).filter(
            TestAttempt.student_id == student.id
        ).order_by(TestAttempt.created_at.desc()).limit(limit).all()
        
        results = []
        for attempt in test_attempts:
            test = db.query(Test).filter(Test.id == attempt.test_id).first()
            analysis = db.query(TestAnalysis).filter(
                TestAnalysis.test_attempt_id == attempt.id
            ).first()
            
            result_item = {
                "test_attempt_id": attempt.id,
                "test_id": attempt.test_id,
                "test_title": test.title if test else "Unknown Test",
                "score": attempt.score,
                "status": attempt.status,
                "attempted_at": attempt.created_at.isoformat(),
                "pass_status": attempt.score >= 70 if attempt.score else False
            }
            
            if analysis:
                result_item["analysis"] = {
                    "overall_percentage": analysis.overall_percentage,
                    "total_questions": analysis.total_questions,
                    "correct_answers": analysis.correct_answers,
                    "incorrect_answers": analysis.incorrect_answers,
                    "strengths": json.loads(analysis.strengths) if analysis.strengths else [],
                    "weaknesses": json.loads(analysis.weaknesses) if analysis.weaknesses else [],
                    "recommendations": json.loads(analysis.recommendations) if analysis.recommendations else []
                }
            
            results.append(result_item)
        
        return {
            "success": True,
            "student_name": student.name,
            "recent_results": results
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
