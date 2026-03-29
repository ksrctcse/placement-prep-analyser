
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, Text, JSON
from datetime import datetime
import enum
from app.database.db import Base

class UserRole(str, enum.Enum):
    STUDENT = "student"
    STAFF = "staff"
    ADMIN = "admin"

class Department(str, enum.Enum):
    CSE = "CSE"
    IT = "IT"
    EEE = "EEE"
    ECE = "ECE"
    MECH = "MECH"
    CIVL = "CIVL"
    CSBS = "CSBS"

class Batch(str, enum.Enum):
    BATCH_2024_2027 = "2024-2027"
    BATCH_2025_2028 = "2025-2028"

class User(Base):
    __tablename__="users"
    id=Column(Integer,primary_key=True)
    name=Column(String,nullable=False)
    email=Column(String,unique=True,nullable=False,index=True)
    password=Column(String,nullable=False)
    role=Column(String,default="student")  # Store as string: 'student', 'staff', 'admin'
    
    # Student-specific fields
    department=Column(String,nullable=True)  # Store as string: 'CSE', 'IT', etc.
    batch=Column(String,nullable=True)  # Store as string: '2024-2027', '2025-2028'
    
    # Staff-specific fields
    staff_id=Column(String,unique=True,nullable=True)
    position=Column(String,nullable=True)
    
    created_at=Column(DateTime,default=datetime.utcnow)
    updated_at=Column(DateTime,default=datetime.utcnow,onupdate=datetime.utcnow)

class Resume(Base):
    __tablename__="resumes"
    id=Column(Integer,primary_key=True)
    user_id=Column(Integer,ForeignKey("users.id"),nullable=False,index=True)
    file_path=Column(String,nullable=False)
    file_name=Column(String)
    
    # Vector store metadata
    vector_store_id=Column(String,nullable=True)  # ID in vector database (ChromaDB/FAISS)
    content_text=Column(Text,nullable=True)  # Extracted text from resume
    
    created_at=Column(DateTime,default=datetime.utcnow)
    updated_at=Column(DateTime,default=datetime.utcnow,onupdate=datetime.utcnow)

class ResumeAnalysis(Base):
    __tablename__="resume_analyses"
    id=Column(Integer,primary_key=True)
    resume_id=Column(Integer,ForeignKey("resumes.id"),nullable=False,index=True)
    user_id=Column(Integer,ForeignKey("users.id"),nullable=False,index=True)
    
    # Analysis results stored as JSON
    analysis_data=Column(JSON,nullable=True)  # Structured analysis from Gemini
    recommendations=Column(JSON,nullable=True)  # Improvement recommendations
    improvement_plan=Column(JSON,nullable=True)  # 30-60-90 day improvement plan
    
    # Analysis metadata
    analysis_status=Column(String,default="pending")  # pending, completed, failed
    vector_chunks_count=Column(Integer,default=0)  # Number of chunks stored in vector DB
    suitability_score=Column(Integer,nullable=True)  # Overall suitability score (0-100)
    
    created_at=Column(DateTime,default=datetime.utcnow)
    updated_at=Column(DateTime,default=datetime.utcnow,onupdate=datetime.utcnow)

class InterviewReport(Base):
    __tablename__="reports"
    id=Column(Integer,primary_key=True)
    user_id=Column(Integer,ForeignKey("users.id"),nullable=False,index=True)
    score=Column(Integer)
    feedback=Column(String)
    interview_type=Column(String)  # e.g., "technical", "hr", "general"
    created_at=Column(DateTime,default=datetime.utcnow)
