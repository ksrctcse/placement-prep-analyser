
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.services.interview_service import generate_question, evaluate_answer
from app.auth.dependencies import get_db, get_student_user, get_current_user
from app.database.models import User, InterviewReport

router = APIRouter(prefix="/interview", tags=["Interview"])

class QuestionResponse(BaseModel):
    question: str
    question_type: str
    difficulty: str

class EvaluateRequest(BaseModel):
    question: str
    answer: str
    question_type: str = "general"

class EvaluateResponse(BaseModel):
    feedback: str
    score: int
    improvements: list

@router.get("/question", response_model=QuestionResponse)
async def get_interview_question(current_user: User = Depends(get_student_user)):
    """
    Generate an interview question for students.
    Only authenticated students can access this.
    """
    question = generate_question()
    return {
        "question": question,
        "question_type": "general",
        "difficulty": "intermediate"
    }

@router.post("/evaluate", response_model=EvaluateResponse)
async def evaluate_interview_answer(
    request: EvaluateRequest,
    current_user: User = Depends(get_student_user),
    db: Session = Depends(get_db)
):
    """
    Evaluate a student's interview answer.
    AI-powered feedback and scoring system.
    Uses Gemini API for evaluation.
    """
    try:
        feedback = evaluate_answer(request.answer)
        
        # Extract score from feedback (assume score is 0-10)
        # This is a simplified approach - enhance based on your feedback format
        score = int(feedback.get("score", 5)) if isinstance(feedback, dict) else 5
        
        # Save evaluation to database
        interview_report = InterviewReport(
            user_id=current_user.id,
            score=score,
            feedback=str(feedback),
            interview_type=request.question_type
        )
        
        db.add(interview_report)
        db.commit()
        
        return EvaluateResponse(
            feedback=str(feedback),
            score=score,
            improvements=[
                "Work on technical depth",
                "Provide more examples",
                "Practice similar questions"
            ]
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error evaluating answer: {str(e)}"
        )

@router.get("/my-interview-history")
async def get_interview_history(
    current_user: User = Depends(get_student_user),
    db: Session = Depends(get_db)
):
    """
    Get interview history for the current student.
    Shows all previous interviews and scores.
    """
    reports = db.query(InterviewReport).filter(
        InterviewReport.user_id == current_user.id
    ).order_by(InterviewReport.created_at.desc()).all()
    
    if not reports:
        return {
            "message": "No interview history",
            "total_interviews": 0,
            "interviews": []
        }
    
    # Calculate average score
    total_score = sum(r.score for r in reports if r.score)
    avg_score = total_score / len([r for r in reports if r.score]) if any(r.score for r in reports) else 0
    
    return {
        "total_interviews": len(reports),
        "average_score": round(avg_score, 2),
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

@router.get("/interview/{interview_id}")
async def get_interview_details(
    interview_id: int,
    current_user: User = Depends(get_student_user),
    db: Session = Depends(get_db)
):
    """
    Get details of a specific interview.
    Students can only view their own interviews.
    """
    report = db.query(InterviewReport).filter(InterviewReport.id == interview_id).first()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found"
        )
    
    # Authorization check
    if report.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own interviews"
        )
    
    return {
        "id": report.id,
        "score": report.score,
        "feedback": report.feedback,
        "interview_type": report.interview_type,
        "created_at": report.created_at.isoformat()
    }

