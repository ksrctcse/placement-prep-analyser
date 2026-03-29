"""
Database initialization script.
Run this script to create all tables in the database.
"""

from app.database.db import engine, Base
from app.database.models import User, Resume, InterviewReport
from app.config.settings import settings

def init_db():
    """Create all tables in the database."""
    print("Dropping existing tables...")
    Base.metadata.drop_all(bind=engine)
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_db()
