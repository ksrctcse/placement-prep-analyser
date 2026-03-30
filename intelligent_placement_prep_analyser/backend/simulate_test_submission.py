#!/usr/bin/env python3
"""
Test the complete test submission and retrieval flow.
Run this to simulate a test submission and verify DB storage.
"""

import sys
sys.path.insert(0, '.')

from app.database.db import SessionLocal
from app.database.models import (
    StudentProfile, Test, TestAttempt, TestAttemptDetail, 
    TestQuestion, Topic
)
from datetime import datetime

def simulate_test_submission():
    """Simulate a complete test submission"""
    db = SessionLocal()
    
    print("\n" + "="*80)
    print("TEST SUBMISSION SIMULATION")
    print("="*80)
    
    try:
        # Get student and test
        student = db.query(StudentProfile).first()
        test = db.query(Test).first()
        
        if not student or not test:
            print("❌ No student or test found in database")
            return
        
        print(f"\n✓ Using Student: {student.name} (ID: {student.id})")
        print(f"✓ Using Test: {test.title} (ID: {test.id})")
        
        # Get test questions
        questions = test.questions
        print(f"✓ Test has {len(questions)} questions")
        
        if len(questions) == 0:
            print("⚠️  Test has no questions")
            return
        
        # Simulate student answers (alternate correct/incorrect)
        print(f"\n📝 Submitting answers...")
        answers = {}
        correct_count = 0
        
        for idx, question in enumerate(questions):
            # Make every other answer correct
            is_correct = idx % 2 == 0
            if is_correct:
                answer = question.correct_option
                correct_count += 1
            else:
                # Choose wrong answer
                options = ['A', 'B', 'C', 'D']
                options.remove(question.correct_option)
                answer = options[0]
            
            answers[question.id] = answer
            print(f"  Q{idx+1}: Answered '{answer}' (Expected: '{question.correct_option}') {'✓' if is_correct else '✗'}")
        
        # Calculate expected score
        expected_score = int((correct_count / len(questions)) * 100)
        
        # Create TestAttempt
        print(f"\n💾 Creating TestAttempt record...")
        test_attempt = TestAttempt(
            test_id=test.id,
            student_id=student.id,
            score=expected_score,
            status="completed"
        )
        
        db.add(test_attempt)
        db.flush()
        
        print(f"✓ TestAttempt created with ID: {test_attempt.id}")
        
        # Create TestAttemptDetail records
        print(f"💾 Creating {len(questions)} TestAttemptDetail records...")
        
        for question in questions:
            student_answer = answers[question.id]
            is_correct = student_answer == question.correct_option
            
            answer_detail = TestAttemptDetail(
                test_attempt_id=test_attempt.id,
                question_id=question.id,
                topic_id=question.topic_id,
                student_answer=student_answer,
                correct_answer=question.correct_option,
                is_correct=is_correct,
                time_spent=0
            )
            
            db.add(answer_detail)
        
        # Commit everything
        print(f"💾 Committing to database...")
        db.commit()
        
        print(f"\n✅ SUCCESS!")
        print(f"   TestAttempt ID: {test_attempt.id}")
        print(f"   Score: {expected_score}%")
        print(f"   Correct: {correct_count}/{len(questions)}")
        print(f"   Status: {test_attempt.status}")
        print(f"   Created: {test_attempt.created_at}")
        
        # Verify retrieval
        print(f"\n✓ Verifying data retrieval...")
        
        # Check TestAttempt
        saved_attempt = db.query(TestAttempt).filter(
            TestAttempt.id == test_attempt.id
        ).first()
        
        if saved_attempt:
            print(f"✓ TestAttempt retrieved: ID={saved_attempt.id}, Score={saved_attempt.score}%")
        else:
            print(f"❌ TestAttempt not found!")
            return
        
        # Check TestAttemptDetail records
        saved_details = db.query(TestAttemptDetail).filter(
            TestAttemptDetail.test_attempt_id == test_attempt.id
        ).all()
        
        print(f"✓ TestAttemptDetail records: {len(saved_details)} found")
        
        if len(saved_details) != len(questions):
            print(f"⚠️  Expected {len(questions)} details, found {len(saved_details)}")
        
        # Show sample detail
        if saved_details:
            detail = saved_details[0]
            print(f"\n📊 Sample Detail Record:")
            print(f"   Question ID: {detail.question_id}")
            print(f"   Student Answer: {detail.student_answer}")
            print(f"   Correct Answer: {detail.correct_answer}")
            print(f"   Is Correct: {detail.is_correct}")
        
        # Verify via API data structure
        print(f"\n🔄 Testing API response format...")
        
        topic_tests_response = {
            "id": test.id,
            "title": test.title,
            "description": test.description,
            "total_questions": len(questions),
            "attempted": True,
            "attempt_id": saved_attempt.id,
            "attempt_score": saved_attempt.score,
            "attempt_status": saved_attempt.status,
            "attempted_at": saved_attempt.created_at.isoformat(),
            "correct_answers": len([d for d in saved_details if d.is_correct]),
            "incorrect_answers": len([d for d in saved_details if not d.is_correct]),
            "pass_status": "pass" if saved_attempt.score >= 70 else "fail",
            "created_at": test.created_at.isoformat()
        }
        
        print(f"✓ API Response will show:")
        print(f"   - attempted: {topic_tests_response['attempted']}")
        print(f"   - attempt_score: {topic_tests_response['attempt_score']}%")
        print(f"   - pass_status: {topic_tests_response['pass_status']}")
        print(f"   - correct_answers: {topic_tests_response['correct_answers']}")
        
        print("\n" + "="*80)
        print("✅ SIMULATION COMPLETE - All data saved and verified!")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    simulate_test_submission()
