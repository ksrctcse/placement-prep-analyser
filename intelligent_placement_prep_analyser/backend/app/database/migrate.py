"""
Database migration script to create all tables
Run this script to initialize the database with PostgreSQL
"""
import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.database.db import Base, engine
from app.database.models import (
    User, Resume, InterviewReport, DepartmentModel, StaffProfile, StudentProfile, 
    Topic, Test, TestAttempt, TestQuestion, TestAttemptDetail, TestAnalysis,
    TopicPerformance, Interview, InterviewAttempt
)


def create_all_tables():
    """Create all database tables"""
    print("Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✓ All tables created successfully!")
        
        # List created tables
        inspector = None
        try:
            from sqlalchemy import inspect
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            print(f"\nCreated tables: {', '.join(tables)}")
        except Exception as e:
            print(f"Could not list tables: {e}")
        
        # Insert default departments if they don't exist
        insert_default_departments()
            
    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        raise


def insert_default_departments():
    """Insert default department values"""
    try:
        from app.database.db import SessionLocal
        from app.database.models import DepartmentModel
        
        session = SessionLocal()
        
        # Check if departments already exist
        existing = session.query(DepartmentModel).first()
        if existing:
            print("✓ Departments already exist")
            session.close()
            return
        
        departments = ["CSE", "IT", "EEE", "ECE", "MECH", "CIVIL"]
        
        for dept_name in departments:
            dept = DepartmentModel(name=dept_name)
            session.add(dept)
        
        session.commit()
        print(f"✓ Inserted {len(departments)} default departments: {', '.join(departments)}")
        session.close()
        
    except Exception as e:
        print(f"✗ Error inserting departments: {e}")


if __name__ == "__main__":
    create_all_tables()
