"""
Database migration script to create all tables
Run this script to initialize the database with PostgreSQL
"""
import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.database.db import Base, engine
from app.database.models import User, Resume, InterviewReport


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
            
    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        raise


if __name__ == "__main__":
    create_all_tables()
