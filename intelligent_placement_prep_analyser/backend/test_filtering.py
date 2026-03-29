#!/usr/bin/env python3
from app.database.db import engine, SessionLocal
from app.database.models import StudentProfile, Topic, DepartmentModel
from sqlalchemy import inspect

def main():
    # Inspect tables
    print("=== STUDENT PROFILES SCHEMA ===")
    inspector = inspect(engine)
    columns = inspector.get_columns('student_profiles')
    for col in columns:
        print(f"  {col['name']}: {col['type']}")

    print("\n=== TOPICS SCHEMA ===")
    columns = inspector.get_columns('topics')
    for col in columns:
        print(f"  {col['name']}: {col['type']}")

    print("\n=== DEPARTMENTS SCHEMA ===")
    columns = inspector.get_columns('departments')
    for col in columns:
        print(f"  {col['name']}: {col['type']}")

    print("\n=== SAMPLE DATA ===")
    db = SessionLocal()
    
    students = db.query(StudentProfile).all()
    print(f"Total students: {len(students)}")
    if students:
        for student in students[:3]:
            print(f"  - {student.name} (Dept ID: {student.department_id}, Section: {student.section})")
    
    topics = db.query(Topic).all()
    print(f"\nTotal topics: {len(topics)}")
    if topics:
        for topic in topics[:5]:
            print(f"  - {topic.title} (Dept ID: {topic.department_id}, Section: {topic.section}, Staff ID: {topic.staff_id})")
    
    print("\n=== FILTERING TEST ===")
    if students and topics:
        student = students[0]
        print(f"Testing with student: {student.name} (Dept {student.department_id}, Section {student.section})")
        
        filtered_topics = db.query(Topic).filter(
            Topic.department_id == student.department_id,
            Topic.section == student.section
        ).all()
        
        print(f"Topics matching this student's department and section: {len(filtered_topics)}")
        for topic in filtered_topics:
            print(f"  - {topic.title}")

if __name__ == "__main__":
    main()
