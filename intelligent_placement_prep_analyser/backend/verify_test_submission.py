#!/usr/bin/env python3
"""
Verify test submission and retrieval flow.
This script checks that test results are correctly saved and retrieved from the database.
"""

import sys
sys.path.insert(0, '.')

from app.database.db import SessionLocal
from app.database.models import StudentProfile, TestAttempt, TestAttemptDetail, Test, Topic
from sqlalchemy.orm import joinedload

def verify_test_submission_flow():
    """Verify that test submissions are saved correctly"""
    db = SessionLocal()
    
    print("\n" + "="*70)
    print("TEST SUBMISSION & RETRIEVAL VERIFICATION")
    print("="*70)
    
    # Check 1: Verify TestAttempt records exist
    print("\n✓ Checking TestAttempt records in database...")
    attempts = db.query(TestAttempt).all()
    print(f"  Total TestAttempt records: {len(attempts)}")
    
    for attempt in attempts:
        print(f"\n  📝 Attempt ID: {attempt.id}")
        print(f"     Test ID: {attempt.test_id}")
        print(f"     Student ID: {attempt.student_id}")
        print(f"     Score: {attempt.score}%")
        print(f"     Status: {attempt.status}")
        print(f"     Created: {attempt.created_at}")
        
        # Get related details
        details = db.query(TestAttemptDetail).filter(
            TestAttemptDetail.test_attempt_id == attempt.id
        ).all()
        print(f"     Answer Details: {len(details)} questions answered")
    
    # Check 2: Verify TestAttemptDetail records
    print("\n✓ Checking TestAttemptDetail records...")
    detail_count = db.query(TestAttemptDetail).count()
    print(f"  Total TestAttemptDetail records: {detail_count}")
    
    # Check 3: Verify data retrieval by student
    print("\n✓ Checking data retrieval by student...")
    students = db.query(StudentProfile).all()
    
    for student in students:
        student_attempts = db.query(TestAttempt).filter(
            TestAttempt.student_id == student.id
        ).all()
        print(f"\n  Student: {student.name} (ID: {student.id})")
        print(f"  Total attempts: {len(student_attempts)}")
        
        for attempt in student_attempts:
            test = db.query(Test).filter(Test.id == attempt.test_id).first()
            print(f"    - Test: {test.title if test else 'Unknown'} (Score: {attempt.score}%)")
    
    # Check 4: Verify topic-wise test retrieval
    print("\n✓ Checking topic-wise test retrieval...")
    topics = db.query(Topic).all()
    
    for topic in topics[:3]:  # Check first 3 topics
        print(f"\n  Topic: {topic.title} (ID: {topic.id})")
        
        # Get tests for this topic
        tests = db.query(Test).filter(
            Test.topics.any(Topic.id == topic.id)
        ).all()
        
        if not tests:
            tests = db.query(Test).filter(Test.topic_id == topic.id).all()
        
        print(f"  Total tests: {len(tests)}")
        
        # Check attempts for each test
        for test in tests:
            attempts = db.query(TestAttempt).filter(
                TestAttempt.test_id == test.id
            ).all()
            print(f"    - {test.title}: {len(attempts)} attempt(s)")
            for attempt in attempts:
                print(f"      Score: {attempt.score}%, Status: {attempt.status}")
    
    # Check 5: Data integrity
    print("\n✓ Checking data integrity...")
    integrity_issues = []
    
    # Check for TestAttempt records without valid test
    orphaned_attempts = db.query(TestAttempt).filter(
        ~TestAttempt.test_id.in_(db.query(Test.id))
    ).all()
    if orphaned_attempts:
        integrity_issues.append(f"Found {len(orphaned_attempts)} orphaned TestAttempt records")
    
    # Check for TestAttempt records without valid student
    invalid_student_attempts = db.query(TestAttempt).filter(
        ~TestAttempt.student_id.in_(db.query(StudentProfile.id))
    ).all()
    if invalid_student_attempts:
        integrity_issues.append(f"Found {len(invalid_student_attempts)} TestAttempt records with invalid student")
    
    # Check for TestAttemptDetail records without valid attempt
    orphaned_details = db.query(TestAttemptDetail).filter(
        ~TestAttemptDetail.test_attempt_id.in_(db.query(TestAttempt.id))
    ).all()
    if orphaned_details:
        integrity_issues.append(f"Found {len(orphaned_details)} orphaned TestAttemptDetail records")
    
    if integrity_issues:
        print("  ⚠️  Issues found:")
        for issue in integrity_issues:
            print(f"     - {issue}")
    else:
        print("  ✓ All data is consistent and valid")
    
    print("\n" + "="*70)
    print("VERIFICATION COMPLETE")
    print("="*70 + "\n")
    
    db.close()

if __name__ == "__main__":
    verify_test_submission_flow()
