"""
Student Performance Routes - Get test results and analyze performance trends
"""
from fastapi import APIRouter, HTTPException, Header
from sqlalchemy.orm import Session, joinedload
from app.database.db import SessionLocal
from app.database.models import (
    StudentProfile, TestAttempt, TestAnalysis, TopicPerformance, Test
)
from app.services.analysis_agent import get_test_analysis
from typing import Optional, List, Dict
from jose import JWTError, jwt
import os
import json

router = APIRouter(prefix="/student/performance", tags=["performance"])

SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
ALGORITHM = "HS256"


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


@router.get("/dashboard-report")
async def get_performance_dashboard_report(
    authorization: Optional[str] = Header(None)
):
    """
    Get comprehensive performance report for student dashboard.
    Includes overall stats, recent tests, topic performance, and trends.
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
        
        # Get all test attempts
        test_attempts = db.query(TestAttempt).filter(
            TestAttempt.student_id == student.id
        ).order_by(TestAttempt.created_at.desc()).all()
        
        # Calculate overall stats
        total_tests = len(test_attempts)
        
        if total_tests == 0:
            return {
                "success": True,
                "student_name": student.name,
                "student_roll": student.roll_number if student.roll_number else f"{student.section}-{student.id:04d}",
                "department": student.department.name if student.department else "Unknown",
                "section": student.section,
                "overall_stats": {
                    "total_tests_taken": 0,
                    "average_score": 0,
                    "total_tests_passed": 0,
                    "pass_rate": 0,
                    "best_score": 0,
                    "worst_score": 0
                },
                "recent_tests": [],
                "topic_performance": [],
                "performance_trend": [],
                "strengths": [],
                "improvements_needed": []
            }
        
        scores = [t.score for t in test_attempts if t.score is not None]
        average_score = int(sum(scores) / len(scores)) if scores else 0
        passed_tests = sum(1 for s in scores if s >= 70)
        pass_rate = int((passed_tests / len(scores)) * 100) if scores else 0
        best_score = max(scores) if scores else 0
        worst_score = min(scores) if scores else 0
        
        # Get recent tests (last 5)
        recent_tests_list = []
        for attempt in test_attempts[:5]:
            test = db.query(Test).filter(Test.id == attempt.test_id).first()
            analysis = get_test_analysis(db, attempt.id)
            
            recent_tests_list.append({
                "test_attempt_id": attempt.id,
                "test_id": attempt.test_id,
                "test_title": test.title if test else "Unknown Test",
                "score": attempt.score,
                "passed": attempt.score >= 70 if attempt.score else False,
                "created_at": attempt.created_at.isoformat() if attempt.created_at else None,
                "strengths": analysis.get("strengths", []) if analysis else [],
                "weaknesses": analysis.get("weaknesses", []) if analysis else []
            })
        
        # Get topic-wise performance
        topic_performance_list = db.query(TopicPerformance).filter(
            TopicPerformance.student_id == student.id
        ).all()
        
        topic_perf_data = []
        for tp in topic_performance_list:
            topic_perf_data.append({
                "topic_id": tp.topic_id,
                "topic_name": tp.topic.title if tp.topic else "Unknown",
                "attempts": tp.total_attempts,
                "average_percentage": tp.average_percentage,
                "last_attempt_percentage": tp.last_attempt_percentage,
                "proficiency_level": tp.proficiency_level,
                "mastery_status": tp.mastery_status,
                "last_attempted": tp.last_attempted_at.isoformat() if tp.last_attempted_at else None
            })
        
        # Sort by average percentage (weakest first)
        topic_perf_data.sort(key=lambda x: x["average_percentage"])
        
        # Get performance trend
        performance_trend = []
        for idx, attempt in enumerate(reversed(test_attempts[-10:])):  # Last 10 attempts
            test = db.query(Test).filter(Test.id == attempt.test_id).first()
            performance_trend.append({
                "attempt_number": idx + 1,
                "test_title": test.title if test else "Test",
                "score": attempt.score,
                "created_at": attempt.created_at.isoformat() if attempt.created_at else None
            })
        
        # Identify strengths and improvements
        strengths = []
        improvements_needed = []
        
        for tp in sorted(topic_perf_data, key=lambda x: x["average_percentage"], reverse=True)[:3]:
            if tp["average_percentage"] >= 80:
                strengths.append(f"{tp['topic_name']}: {tp['average_percentage']}% mastery")
        
        for tp in sorted(topic_perf_data, key=lambda x: x["average_percentage"])[:3]:
            if tp["average_percentage"] < 70:
                improvements_needed.append(f"{tp['topic_name']}: {tp['average_percentage']}% (needs practice)")
        
        return {
            "success": True,
            "student_name": student.name,
            "student_roll": student.roll_number if student.roll_number else f"{student.section}-{student.id:04d}",
            "department": student.department.name if student.department else "Unknown",
            "section": student.section,
            "overall_stats": {
                "total_tests_taken": total_tests,
                "average_score": average_score,
                "total_tests_passed": passed_tests,
                "pass_rate": pass_rate,
                "best_score": best_score,
                "worst_score": worst_score
            },
            "recent_tests": recent_tests_list,
            "topic_performance": topic_perf_data,
            "performance_trend": performance_trend,
            "strengths": strengths,
            "improvements_needed": improvements_needed
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting performance report: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/topic-performance/{topic_id}")
async def get_topic_performance(
    topic_id: int,
    authorization: Optional[str] = Header(None)
):
    """Get performance details for a specific topic"""
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
        
        # Get topic performance
        topic_perf = db.query(TopicPerformance).filter(
            TopicPerformance.student_id == student.id,
            TopicPerformance.topic_id == topic_id
        ).first()
        
        if not topic_perf:
            raise HTTPException(status_code=404, detail="No performance data for this topic")
        
        return {
            "success": True,
            "topic_id": topic_perf.topic_id,
            "topic_name": topic_perf.topic.title if topic_perf.topic else "Unknown",
            "total_attempts": topic_perf.total_attempts,
            "total_questions": topic_perf.total_questions,
            "correct_answers": topic_perf.correct_answers,
            "average_percentage": topic_perf.average_percentage,
            "last_attempt_percentage": topic_perf.last_attempt_percentage,
            "proficiency_level": topic_perf.proficiency_level,
            "mastery_status": topic_perf.mastery_status,
            "last_attempted": topic_perf.last_attempted_at.isoformat() if topic_perf.last_attempted_at else None
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/test-attempts")
async def get_all_test_attempts(
    limit: int = 10,
    offset: int = 0,
    authorization: Optional[str] = Header(None)
):
    """Get all test attempts for a student with pagination"""
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
        
        # Get test attempts with pagination
        total_attempts = db.query(TestAttempt).filter(
            TestAttempt.student_id == student.id
        ).count()
        
        test_attempts = db.query(TestAttempt).filter(
            TestAttempt.student_id == student.id
        ).order_by(TestAttempt.created_at.desc()).offset(offset).limit(limit).all()
        
        attempts_list = []
        for attempt in test_attempts:
            test = db.query(Test).filter(Test.id == attempt.test_id).first()
            analysis = get_test_analysis(db, attempt.id)
            
            attempts_list.append({
                "test_attempt_id": attempt.id,
                "test_id": attempt.test_id,
                "test_title": test.title if test else "Unknown Test",
                "score": attempt.score,
                "passed": attempt.score >= 70 if attempt.score else False,
                "status": attempt.status,
                "created_at": attempt.created_at.isoformat() if attempt.created_at else None,
                "analysis_available": analysis is not None
            })
        
        return {
            "success": True,
            "total_attempts": total_attempts,
            "limit": limit,
            "offset": offset,
            "attempts": attempts_list
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
