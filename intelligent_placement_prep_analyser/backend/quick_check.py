#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')

from app.database.db import SessionLocal
from app.database.models import StudentProfile, TestAttempt, Test

db = SessionLocal()
students = db.query(StudentProfile).count()
tests = db.query(Test).count()
attempts = db.query(TestAttempt).count()
print(f'Students: {students}')
print(f'Tests: {tests}')
print(f'Test Attempts: {attempts}')

if attempts > 0:
    print("\nTest attempts found:")
    for a in db.query(TestAttempt).all():
        print(f"  - ID {a.id}: Student {a.student_id}, Test {a.test_id}")

db.close()
