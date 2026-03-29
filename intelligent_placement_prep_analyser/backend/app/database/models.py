
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
