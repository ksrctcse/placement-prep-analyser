#!/usr/bin/env python3
"""
Diagnostic script to check test attempts in the database
"""
import sys
sys.path.insert(0, 'intelligent_placement_prep_analyser/backend')

from app.database.db import SessionLocal
from app.database.models import StudentProfile, TestAttempt, TestAttemptDetail, Test
from sqlalchemy.orm import joinedload

db = SessionLocal()

try:
    print("=" * 70)
    print("📊 TEST ATTEMPTS DIAGNOSTIC")
    print("=" * 70)
    
    # Check all students
    students = db.query(StudentProfile).all()
    print(f"\n👥 Total Students: {len(students)}")
    
    if students:
        for student in students:
            print(f"\n{'─' * 70}")
            print(f"Student: {student.name} (ID: {student.id})")
            
            # Check test attempts
            test_attempts = db.query(TestAttempt).filter(
                TestAttempt.student_id == student.id
            ).order_by(TestAttempt.created_at.desc()).all()
            
            print(f"  📝 Test Attempts: {len(test_attempts)}")
            
            if test_attempts:
                for ta in test_attempts:
                    test = db.query(Test).filter(Test.id == ta.test_id).first()
                    correct = db.query(TestAttemptDetail).filter(
                        TestAttemptDetail.test_attempt_id == ta.id,
                        TestAttemptDetail.is_correct == True
                    ).count()
                    total = db.query(TestAttemptDetail).filter(
                        TestAttemptDetail.test_attempt_id == ta.id
                    ).count()
                    
                pct = int((correct / total) * 100) if total > 0 else 0
                    print(f"    • Test ID {ta.test_id}: {test.title if test else 'Unknown'}")
                    print(f"      Score: {ta.score}%, Percentage: {pct}%, Correct: {correct}/{total}")
                    print(f"      Status: {ta.status}, Attempt ID: {ta.id}")
                    print(f"      Created: {ta.created_at}")
            else:
                print("  ⚠️  No test attempts found - student hasn't taken any tests yet")
    
    print(f"\n{'=' * 70}")
    print("✅ Diagnostic Complete")
    print("=" * 70)
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
