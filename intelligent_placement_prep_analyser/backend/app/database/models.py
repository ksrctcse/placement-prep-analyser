
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.database.db import Base
from datetime import datetime
import enum

class DepartmentModel(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)  # CSE, IT, EEE, ECE, MECH, CIVIL
    
    staff = relationship("StaffProfile", back_populates="department")
    students = relationship("StudentProfile", back_populates="department")

class UserRole(str, enum.Enum):
    STAFF = "staff"
    STUDENT = "student"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    staff_profile = relationship("StaffProfile", back_populates="user", uselist=False)
    student_profile = relationship("StudentProfile", back_populates="user", uselist=False)
    resumes = relationship("Resume", back_populates="user")
    reports = relationship("InterviewReport", back_populates="user")

class StaffProfile(Base):
    __tablename__ = "staff_profiles"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    name = Column(String, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="staff_profile")
    department = relationship("DepartmentModel", back_populates="staff")
    topics = relationship("Topic", back_populates="staff", foreign_keys="Topic.staff_id")
    tests = relationship("Test", back_populates="staff", foreign_keys="Test.staff_id")
    interviews = relationship("Interview", back_populates="staff", foreign_keys="Interview.staff_id")

class StudentProfile(Base):
    __tablename__ = "student_profiles"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    name = Column(String, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    section = Column(String(1), nullable=False)  # A, B, C
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="student_profile")
    department = relationship("DepartmentModel", back_populates="students")
    test_attempts = relationship("TestAttempt", back_populates="student")
    interview_attempts = relationship("InterviewAttempt", back_populates="student")

class Resume(Base):
    __tablename__ = "resumes"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_path = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="resumes")

class InterviewReport(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    score = Column(Integer)
    feedback = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="reports")


class Topic(Base):
    __tablename__ = "topics"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer)  # in bytes
    staff_id = Column(Integer, ForeignKey("staff_profiles.id"), nullable=False, index=True)
    is_indexed = Column(Boolean, default=False)  # RAG: Whether topic has been embedded
    embedding_chunks = Column(Integer, default=0)  # RAG: Number of text chunks from PDF
    last_indexed_at = Column(DateTime, nullable=True)  # RAG: When embeddings were created
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    staff = relationship("StaffProfile", foreign_keys=[staff_id])


class Test(Base):
    __tablename__ = "tests"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String)
    topic_id = Column(Integer, ForeignKey("topics.id"))
    staff_id = Column(Integer, ForeignKey("staff_profiles.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    staff = relationship("StaffProfile", foreign_keys=[staff_id])
    topic = relationship("Topic", foreign_keys=[topic_id])


class TestAttempt(Base):
    __tablename__ = "test_attempts"
    id = Column(Integer, primary_key=True)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"), nullable=False, index=True)
    score = Column(Integer)
    status = Column(String, default="completed")  # pending, completed, in_progress
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    test = relationship("Test", foreign_keys=[test_id])
    student = relationship("StudentProfile", foreign_keys=[student_id])


class Interview(Base):
    __tablename__ = "interviews"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String)
    topic_id = Column(Integer, ForeignKey("topics.id"))
    staff_id = Column(Integer, ForeignKey("staff_profiles.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    staff = relationship("StaffProfile", foreign_keys=[staff_id])
    topic = relationship("Topic", foreign_keys=[topic_id])


class InterviewAttempt(Base):
    __tablename__ = "interview_attempts"
    id = Column(Integer, primary_key=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"), nullable=False, index=True)
    score = Column(Integer)
    feedback = Column(String)
    status = Column(String, default="completed")  # pending, in_progress, completed
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    interview = relationship("Interview", foreign_keys=[interview_id])
    student = relationship("StudentProfile", foreign_keys=[student_id])
