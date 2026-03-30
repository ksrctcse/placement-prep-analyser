
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Enum as SQLEnum, Text, Table
from sqlalchemy.orm import relationship
from app.database.db import Base
from datetime import datetime
import enum

# Association table for many-to-many relationship between Tests and Topics
test_topics_association = Table(
    'test_topics',
    Base.metadata,
    Column('test_id', Integer, ForeignKey('tests.id'), primary_key=True),
    Column('topic_id', Integer, ForeignKey('topics.id'), primary_key=True)
)

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
    created_tests = relationship("Test", back_populates="created_by_student", foreign_keys="Test.created_by_student_id")

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
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True, index=True)
    section = Column(String(1), nullable=True)  # A, B, or C
    is_indexed = Column(Boolean, default=False)  # RAG: Whether topic has been embedded
    embedding_chunks = Column(Integer, default=0)  # RAG: Number of text chunks from PDF
    last_indexed_at = Column(DateTime, nullable=True)  # RAG: When embeddings were created
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    staff = relationship("StaffProfile", foreign_keys=[staff_id])
    department = relationship("DepartmentModel", foreign_keys=[department_id])


class Test(Base):
    __tablename__ = "tests"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String)
    topic_id = Column(Integer, ForeignKey("topics.id"))  # Backward compatibility: single topic
    staff_id = Column(Integer, ForeignKey("staff_profiles.id"), index=True)  # Optional: staff-created
    created_by_student_id = Column(Integer, ForeignKey("student_profiles.id"), index=True)  # Student-created tests
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    staff = relationship("StaffProfile", foreign_keys=[staff_id])
    topic = relationship("Topic", foreign_keys=[topic_id], primaryjoin="Test.topic_id == Topic.id")
    topics = relationship("Topic", secondary=test_topics_association)  # Many-to-many: topics
    created_by_student = relationship("StudentProfile", back_populates="created_tests", foreign_keys=[created_by_student_id])
    questions = relationship("TestQuestion", back_populates="test")


class TestQuestion(Base):
    __tablename__ = "test_questions"
    id = Column(Integer, primary_key=True)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=False, index=True)
    question_text = Column(Text, nullable=False)
    option_a = Column(String, nullable=False)
    option_b = Column(String, nullable=False)
    option_c = Column(String, nullable=False)
    option_d = Column(String, nullable=False)
    correct_option = Column(String, nullable=False)  # A, B, C, D
    explanation = Column(Text)
    topic_id = Column(Integer, ForeignKey("topics.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    test = relationship("Test", back_populates="questions")
    topic = relationship("Topic")


class TestAttempt(Base):
    __tablename__ = "test_attempts"
    id = Column(Integer, primary_key=True)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"), nullable=False, index=True)
    score = Column(Integer)
    status = Column(String, default="completed")  # pending, completed, in_progress
    attempt_count = Column(Integer, default=1)  # Track how many times this test has been attempted
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


class TestAttemptDetail(Base):
    """Stores answer details for each question in a test attempt"""
    __tablename__ = "test_attempt_details"
    id = Column(Integer, primary_key=True)
    test_attempt_id = Column(Integer, ForeignKey("test_attempts.id"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("test_questions.id"), nullable=False, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False, index=True)
    student_answer = Column(String)  # A, B, C, D or None
    correct_answer = Column(String)  # A, B, C, D
    is_correct = Column(Boolean, default=False)
    time_spent = Column(Integer, default=0)  # in seconds
    created_at = Column(DateTime, default=datetime.utcnow)
    
    test_attempt = relationship("TestAttempt", foreign_keys=[test_attempt_id])
    question = relationship("TestQuestion", foreign_keys=[question_id])
    topic = relationship("Topic", foreign_keys=[topic_id])


class TestAnalysis(Base):
    """Stores analysis results for a test attempt"""
    __tablename__ = "test_analyses"
    id = Column(Integer, primary_key=True)
    test_attempt_id = Column(Integer, ForeignKey("test_attempts.id"), nullable=False, unique=True, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"), nullable=False, index=True)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=False, index=True)
    
    # Overall metrics
    total_questions = Column(Integer)
    correct_answers = Column(Integer)
    incorrect_answers = Column(Integer)
    unanswered = Column(Integer, default=0)
    overall_percentage = Column(Integer)  # 0-100
    pass_status = Column(Boolean, default=False)  # True if >= 70%
    
    # Analysis content
    strengths = Column(Text)  # JSON: list of topics/concepts done well
    weaknesses = Column(Text)  # JSON: list of topics/concepts that need improvement
    recommendations = Column(Text)  # JSON: suggestions for improvement
    topic_wise_analysis = Column(Text)  # JSON: performance breakdown by topic
    
    # Metadata
    analysis_generated_by = Column(String, default="ai_agent")  # ai_agent, manual, etc.
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    test_attempt = relationship("TestAttempt", foreign_keys=[test_attempt_id])
    student = relationship("StudentProfile", foreign_keys=[student_id])
    test = relationship("Test", foreign_keys=[test_id])


class TopicPerformance(Base):
    """Tracks performance per topic for a student"""
    __tablename__ = "topic_performance"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"), nullable=False, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)
    section = Column(String(1), nullable=False)
    
    # Performance metrics
    total_attempts = Column(Integer, default=0)
    total_questions = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    average_percentage = Column(Integer, default=0)  # 0-100
    last_attempt_percentage = Column(Integer, default=0)
    
    # Proficiency level
    proficiency_level = Column(String(20), default="beginner")  # beginner, intermediate, advanced, expert
    mastery_status = Column(Boolean, default=False)  # True if consistently >= 80%
    
    # Tracking
    last_attempted_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    student = relationship("StudentProfile", foreign_keys=[student_id])
    topic = relationship("Topic", foreign_keys=[topic_id])
    department = relationship("DepartmentModel", foreign_keys=[department_id])
