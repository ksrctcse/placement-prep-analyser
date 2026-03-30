"""
Test Analysis Agent - Analyzes test performance and generates insights using AI
Identifies strengths, weaknesses, and provides recommendations
"""

import json
import google.generativeai as genai
from app.config.settings import settings
from sqlalchemy.orm import Session
from app.database.models import (
    TestAttempt, TestAttemptDetail, TestAnalysis, Test, TestQuestion, 
    Topic, TopicPerformance, StudentProfile
)
from typing import Dict, List, Optional
from datetime import datetime

genai.configure(api_key=settings.GOOGLE_API_KEY)
# Use gemini-2.5-flash (newest, fastest, and available in your API tier)
# Available options in your account: gemini-2.5-flash, gemini-2.0-flash, gemini-2.5-pro
try:
    model = genai.GenerativeModel("gemini-2.5-flash")
except:
    # Fallback to gemini-2.0-flash if 2.5 not available
    model = genai.GenerativeModel("gemini-2.0-flash")


def analyze_test_performance(
    db: Session,
    test_attempt_id: int
) -> Dict:
    """
    Analyze test performance using AI agent.
    Generates insights about strengths, weaknesses, and recommendations.
    
    Args:
        db: Database session
        test_attempt_id: ID of the test attempt to analyze
    
    Returns:
        Dictionary with analysis results
    """
    
    # Get test attempt
    test_attempt = db.query(TestAttempt).filter(
        TestAttempt.id == test_attempt_id
    ).first()
    
    if not test_attempt:
        return {"error": "Test attempt not found"}
    
    # Get test details with questions
    test = db.query(Test).filter(Test.id == test_attempt.test_id).first()
    
    # Get answer details
    answer_details = db.query(TestAttemptDetail).filter(
        TestAttemptDetail.test_attempt_id == test_attempt_id
    ).all()
    
    if not answer_details:
        return {"error": "No answer details found for this test attempt"}
    
    # Get student info
    student = db.query(StudentProfile).filter(
        StudentProfile.id == test_attempt.student_id
    ).first()
    
    # Calculate metrics
    total_questions = len(answer_details)
    correct_answers = sum(1 for ad in answer_details if ad.is_correct)
    incorrect_answers = sum(1 for ad in answer_details if not ad.is_correct)
    overall_percentage = int((correct_answers / total_questions) * 100) if total_questions > 0 else 0
    pass_status = overall_percentage >= 70
    
    # Analyze by topic
    topic_performance = _analyze_by_topic(db, answer_details)
    
    # Generate AI insights
    try:
        ai_analysis = _generate_ai_analysis(
            test_title=test.title,
            total_questions=total_questions,
            correct_answers=correct_answers,
            overall_percentage=overall_percentage,
            topic_performance=topic_performance,
            student_name=student.name if student else "Student",
            department=student.department.name if student and student.department else "Unknown"
        )
    except Exception as e:
        print(f"Error generating AI analysis: {e}")
        ai_analysis = _create_fallback_analysis(
            overall_percentage=overall_percentage,
            topic_performance=topic_performance
        )
    
    # Create TestAnalysis record
    analysis = TestAnalysis(
        test_attempt_id=test_attempt_id,
        student_id=test_attempt.student_id,
        test_id=test_attempt.test_id,
        total_questions=total_questions,
        correct_answers=correct_answers,
        incorrect_answers=incorrect_answers,
        unanswered=0,
        overall_percentage=overall_percentage,
        pass_status=pass_status,
        strengths=json.dumps(ai_analysis.get("strengths", [])),
        weaknesses=json.dumps(ai_analysis.get("weaknesses", [])),
        recommendations=json.dumps(ai_analysis.get("recommendations", [])),
        topic_wise_analysis=json.dumps(topic_performance),
        analysis_generated_by="ai_agent"
    )
    
    db.add(analysis)
    
    # Update topic performance for student
    _update_topic_performance(db, test_attempt.student_id, topic_performance, student)
    
    db.commit()
    
    return {
        "success": True,
        "test_attempt_id": test_attempt_id,
        "test_title": test.title,
        "student_name": student.name if student else "Unknown",
        "overall_percentage": overall_percentage,
        "pass_status": pass_status,
        "total_questions": total_questions,
        "correct_answers": correct_answers,
        "incorrect_answers": incorrect_answers,
        "strengths": ai_analysis.get("strengths", []),
        "weaknesses": ai_analysis.get("weaknesses", []),
        "recommendations": ai_analysis.get("recommendations", []),
        "topic_wise_performance": topic_performance,
        "passed": pass_status,
        "score_message": "Excellent performance!" if overall_percentage >= 80 else (
            "Good job! Keep practicing." if overall_percentage >= 70 else (
                "You need more practice in these areas."
            )
        )
    }


def _analyze_by_topic(db: Session, answer_details: List[TestAttemptDetail]) -> Dict:
    """Analyze performance by individual topics"""
    
    topic_performance = {}
    
    for detail in answer_details:
        topic_id = detail.topic_id
        if topic_id not in topic_performance:
            topic_performance[topic_id] = {
                "topic_id": topic_id,
                "topic_name": detail.topic.title if detail.topic else "Unknown",
                "total_questions": 0,
                "correct_answers": 0,
                "percentage": 0
            }
        
        topic_performance[topic_id]["total_questions"] += 1
        if detail.is_correct:
            topic_performance[topic_id]["correct_answers"] += 1
    
    # Calculate percentages
    for topic_id in topic_performance:
        total = topic_performance[topic_id]["total_questions"]
        correct = topic_performance[topic_id]["correct_answers"]
        topic_performance[topic_id]["percentage"] = int((correct / total) * 100) if total > 0 else 0
    
    return topic_performance


def _generate_ai_analysis(
    test_title: str,
    total_questions: int,
    correct_answers: int,
    overall_percentage: int,
    topic_performance: Dict,
    student_name: str,
    department: str
) -> Dict:
    """Generate AI-powered analysis using Gemini"""
    
    # Prepare topic performance summary
    topic_summary = "\n".join([
        f"- {info['topic_name']}: {info['percentage']}% ({info['correct_answers']}/{info['total_questions']} correct)"
        for info in sorted(topic_performance.values(), key=lambda x: x['percentage'])
    ])
    
    prompt = f"""You are an expert educator analyzing a student's test performance.

Student: {student_name}
Department: {department}
Test: {test_title}

Test Results:
- Total Questions: {total_questions}
- Correct Answers: {correct_answers}
- Overall Score: {overall_percentage}%
- Status: {'PASSED' if overall_percentage >= 70 else 'NEEDS IMPROVEMENT'}

Performance by Topic:
{topic_summary}

Based on this performance data, provide:

1. **Strengths** (2-3 areas where the student did well):
   - List topics/concepts the student mastered

2. **Weaknesses** (2-3 areas needing improvement):
   - List topics/concepts that need more practice

3. **Recommendations** (3-4 specific, actionable suggestions):
   - Provide concrete steps to improve performance
   - Focus on weak areas
   - Suggest learning strategies

Format your response as a JSON object with keys: "strengths" (array), "weaknesses" (array), "recommendations" (array).
Each item should be a clear string. Return ONLY valid JSON, nothing else.

Example format:
{{
    "strengths": [
        "Strong understanding of topic A",
        "Good application of concept B"
    ],
    "weaknesses": [
        "Needs more practice on advanced concepts",
        "Should review fundamentals of topic C"
    ],
    "recommendations": [
        "Practice more questions on topic C",
        "Review the vector notes materials",
        "Attempt 5 more tests focusing on weak areas"
    ]
}}"""

    try:
        response = model.generate_content(prompt)
        
        # Parse JSON response
        try:
            analysis_data = json.loads(response.text)
            
            # Validate structure
            if all(key in analysis_data for key in ["strengths", "weaknesses", "recommendations"]):
                return {
                    "strengths": analysis_data.get("strengths", []),
                    "weaknesses": analysis_data.get("weaknesses", []),
                    "recommendations": analysis_data.get("recommendations", [])
                }
        except json.JSONDecodeError:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                try:
                    analysis_data = json.loads(json_match.group())
                    return {
                        "strengths": analysis_data.get("strengths", []),
                        "weaknesses": analysis_data.get("weaknesses", []),
                        "recommendations": analysis_data.get("recommendations", [])
                    }
                except json.JSONDecodeError:
                    pass
        
        return _create_fallback_analysis(overall_percentage, {"default": {"percentage": overall_percentage}})
    
    except Exception as e:
        print(f"Error in AI analysis: {e}")
        return _create_fallback_analysis(overall_percentage, {"default": {"percentage": overall_percentage}})


def _create_fallback_analysis(overall_percentage: int, topic_performance: Dict) -> Dict:
    """Create fallback analysis when AI generation fails"""
    
    # Find weak topics
    weak_topics = [info for info in topic_performance.values() if info.get("percentage", 0) < 70]
    strong_topics = [info for info in topic_performance.values() if info.get("percentage", 100) >= 80]
    
    weak_topic_names = [t.get("topic_name", "Unknown") for t in weak_topics[:2]]
    strong_topic_names = [t.get("topic_name", "Unknown") for t in strong_topics[:2]]
    
    return {
        "strengths": [
            f"Good understanding of {', '.join(strong_topic_names)}" if strong_topic_names else "Basic concepts understood"
        ],
        "weaknesses": [
            f"Need more practice on {', '.join(weak_topic_names)}" if weak_topic_names else "Some topics need review"
        ],
        "recommendations": [
            "Review topics where you scored less than 70%",
            "Practice more questions on weak topics",
            "Take another test after studying weak areas",
            "Ask for help from instructors or peers"
        ]
    }


def _update_topic_performance(
    db: Session,
    student_id: int,
    topic_performance: Dict,
    student: StudentProfile
) -> None:
    """Update TopicPerformance records based on test results"""
    
    for topic_id_str, perf_data in topic_performance.items():
        try:
            topic_id = int(topic_id_str)
        except (ValueError, TypeError):
            continue
        
        # Get or create TopicPerformance record
        topic_perf = db.query(TopicPerformance).filter(
            TopicPerformance.student_id == student_id,
            TopicPerformance.topic_id == topic_id
        ).first()
        
        if not topic_perf:
            topic_perf = TopicPerformance(
                student_id=student_id,
                topic_id=topic_id,
                department_id=student.department_id,
                section=student.section,
                total_attempts=0,
                total_questions=0,
                correct_answers=0,
                average_percentage=0,
                last_attempt_percentage=0,
                proficiency_level="beginner",
                mastery_status=False
            )
            db.add(topic_perf)
        
        # Update performance metrics
        total_q = perf_data.get("total_questions", 0)
        correct_q = perf_data.get("correct_answers", 0)
        percentage = perf_data.get("percentage", 0)
        
        # Ensure fields are initialized (in case they're None)
        if topic_perf.total_attempts is None:
            topic_perf.total_attempts = 0
        if topic_perf.total_questions is None:
            topic_perf.total_questions = 0
        if topic_perf.correct_answers is None:
            topic_perf.correct_answers = 0
        
        topic_perf.total_attempts += 1
        topic_perf.total_questions += total_q
        topic_perf.correct_answers += correct_q
        topic_perf.last_attempt_percentage = percentage
        topic_perf.last_attempted_at = datetime.utcnow()
        
        # Calculate new average
        if topic_perf.total_questions > 0:
            topic_perf.average_percentage = int((topic_perf.correct_answers / topic_perf.total_questions) * 100)
        
        # Update proficiency level
        if topic_perf.average_percentage >= 90:
            topic_perf.proficiency_level = "expert"
            topic_perf.mastery_status = True
        elif topic_perf.average_percentage >= 80:
            topic_perf.proficiency_level = "advanced"
            topic_perf.mastery_status = True
        elif topic_perf.average_percentage >= 65:
            topic_perf.proficiency_level = "intermediate"
        else:
            topic_perf.proficiency_level = "beginner"
            topic_perf.mastery_status = False
    
    db.commit()


def get_test_analysis(db: Session, test_attempt_id: int) -> Optional[Dict]:
    """Retrieve stored test analysis"""
    
    analysis = db.query(TestAnalysis).filter(
        TestAnalysis.test_attempt_id == test_attempt_id
    ).first()
    
    if not analysis:
        return None
    
    return {
        "test_attempt_id": analysis.test_attempt_id,
        "overall_percentage": analysis.overall_percentage,
        "pass_status": analysis.pass_status,
        "correct_answers": analysis.correct_answers,
        "total_questions": analysis.total_questions,
        "incorrect_answers": analysis.incorrect_answers,
        "strengths": json.loads(analysis.strengths) if analysis.strengths else [],
        "weaknesses": json.loads(analysis.weaknesses) if analysis.weaknesses else [],
        "recommendations": json.loads(analysis.recommendations) if analysis.recommendations else [],
        "topic_wise_analysis": json.loads(analysis.topic_wise_analysis) if analysis.topic_wise_analysis else {},
        "created_at": analysis.created_at.isoformat() if analysis.created_at else None
    }
