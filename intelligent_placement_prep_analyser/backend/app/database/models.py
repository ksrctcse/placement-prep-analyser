
from sqlalchemy import Column,Integer,String,ForeignKey
from app.database.db import Base

class User(Base):
    __tablename__="users"
    id=Column(Integer,primary_key=True)
    name=Column(String)
    email=Column(String,unique=True)
    password=Column(String)
    role=Column(String)
    department=Column(String)

class Resume(Base):
    __tablename__="resumes"
    id=Column(Integer,primary_key=True)
    user_id=Column(Integer,ForeignKey("users.id"))
    file_path=Column(String)

class InterviewReport(Base):
    __tablename__="reports"
    id=Column(Integer,primary_key=True)
    user_id=Column(Integer)
    score=Column(Integer)
    feedback=Column(String)
