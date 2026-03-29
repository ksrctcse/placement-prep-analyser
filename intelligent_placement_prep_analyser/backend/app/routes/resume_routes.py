
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, field_serializer
from typing import Optional, List, Dict, Any
from datetime import datetime
import os
from app.services.resume_service import process_resume, analyze_resume_with_gemini, generate_improvement_plan
from app.services.vector_store_service import get_vector_store
from app.auth.dependencies import get_db, get_current_user, get_student_user
from app.database.models import User, Resume, ResumeAnalysis

router = APIRouter(prefix="/resume", tags=["Resume"])

class ResumeResponse(BaseModel):
    id: int
    user_id: int
    file_name: str
    file_path: str
    file_size: int  # Size in bytes
    vector_store_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, value: datetime) -> str:
        return value.isoformat() if value else None

    class Config:
        from_attributes = True

class ResumeAnalysisResponse(BaseModel):
    id: int
    resume_id: int
    user_id: int
    analysis_data: Optional[Dict[str, Any]]
    recommendations: Optional[List[Dict[str, str]]]
    improvement_plan: Optional[Dict[str, Any]]
    analysis_status: str
    suitability_score: Optional[int]
    vector_chunks_count: int
    created_at: datetime
    updated_at: datetime

    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, value: datetime) -> str:
        return value.isoformat() if value else None

    class Config:
        from_attributes = True

class ResumeSearchRequest(BaseModel):
    query: str
    top_k: int = 5

@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_student_user),
    db: Session = Depends(get_db)
):
    """
    Upload and process a resume with Gemini AI analysis.
    - Extracts text from PDF
    - Analyzes with Google Gemini AI
    - Stores in vector database for semantic search
    - Generates recommendations and improvement plan
    """
    try:
        # Check if user already has a resume
        existing_resume = db.query(Resume).filter(Resume.user_id == current_user.id).first()
        
        # Process resume and extract text
        result = await process_resume(file)
        resume_text = result.get("text", "")
        file_path = result.get("file_path", "")
        
        # Save resume metadata to database
        resume_record = Resume(
            user_id=current_user.id,
            file_name=file.filename,
            file_path=file_path,
            content_text=resume_text,
            vector_store_id=None  # Will be set after analysis
        )
        
        # If updating existing resume, delete the old one and its analyses
        if existing_resume:
            # First delete all associated analyses
            db.query(ResumeAnalysis).filter(ResumeAnalysis.resume_id == existing_resume.id).delete()
            # Then delete the resume itself
            db.delete(existing_resume)
        
        db.add(resume_record)
        db.commit()
        db.refresh(resume_record)
        
        # Analyze resume with Gemini
        analysis_result = await analyze_resume_with_gemini(
            resume_text,
            current_user.id,
            file.filename
        )
        
        # Generate improvement plan
        improvement_plan = None
        if analysis_result.get("analysis_status") == "completed":
            improvement_plan = await generate_improvement_plan(analysis_result)
        
        # Save analysis to database
        analysis_record = ResumeAnalysis(
            resume_id=resume_record.id,
            user_id=current_user.id,
            analysis_data=analysis_result.get("analysis"),
            recommendations=analysis_result.get("recommendations"),
            improvement_plan=improvement_plan,
            analysis_status=analysis_result.get("analysis_status", "completed"),
            suitability_score=analysis_result.get("analysis", {}).get("suitability_score"),
            vector_chunks_count=analysis_result.get("vector_chunks_count", 0)
        )
        
        db.add(analysis_record)
        db.commit()
        db.refresh(analysis_record)
        
        return {
            "message": "Resume uploaded and analyzed successfully",
            "resume_id": resume_record.id,
            "analysis_id": analysis_record.id,
            "file_name": file.filename,
            "analysis_status": analysis_result.get("analysis_status"),
            "suitability_score": analysis_result.get("analysis", {}).get("suitability_score"),
            "vector_chunks_count": analysis_result.get("vector_chunks_count", 0)
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error processing resume: {str(e)}"
        )

@router.get("/my-resume")
async def get_my_resume(
    current_user: User = Depends(get_student_user),
    db: Session = Depends(get_db)
):
    """
    Get the current student's resume.
    Returns HTTP 300 if no resume found, HTTP 200 with resume details if found.
    """
    resume = db.query(Resume).filter(Resume.user_id == current_user.id).first()
    
    if not resume:
        return JSONResponse(
            status_code=300,
            content={
                "has_resume": False,
                "message": "No resumes found",
                "resumes": []
            }
        )
    
    # Calculate file size
    file_size = 0
    if os.path.exists(resume.file_path):
        file_size = os.path.getsize(resume.file_path)
    
    return JSONResponse(
        status_code=200,
        content={
            "has_resume": True,
            "resume": {
                "id": resume.id,
                "user_id": resume.user_id,
                "file_name": resume.file_name,
                "file_path": resume.file_path,
                "file_size": file_size,
                "vector_store_id": resume.vector_store_id,
                "created_at": resume.created_at.isoformat() if resume.created_at else None,
                "updated_at": resume.updated_at.isoformat() if resume.updated_at else None
            },
            "message": "Resume found"
        }
    )

@router.get("/list/my-resumes")
async def list_my_resumes(
    current_user: User = Depends(get_student_user),
    db: Session = Depends(get_db)
):
    """
    List all resumes for the current student with file sizes and dates.
    """
    resumes = db.query(Resume).filter(Resume.user_id == current_user.id).all()
    
    resume_list = []
    for resume in resumes:
        file_size = 0
        if os.path.exists(resume.file_path):
            file_size = os.path.getsize(resume.file_path)
        
        resume_list.append({
            "id": resume.id,
            "user_id": resume.user_id,
            "file_name": resume.file_name,
            "file_path": resume.file_path,
            "file_size": file_size,
            "vector_store_id": resume.vector_store_id,
            "created_at": resume.created_at.isoformat() if resume.created_at else None,
            "updated_at": resume.updated_at.isoformat() if resume.updated_at else None
        })
    
    return JSONResponse(
        status_code=200,
        content={
            "total_resumes": len(resume_list),
            "resumes": resume_list
        }
    )

@router.get("/{user_id}", response_model=ResumeResponse)
async def get_user_resume(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific user's resume (public endpoint for staff).
    """
    resume = db.query(Resume).filter(Resume.user_id == user_id).first()
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found for this user"
        )
    
    return resume

@router.get("/analysis/my-analysis")
async def get_my_resume_analysis(
    current_user: User = Depends(get_student_user),
    db: Session = Depends(get_db)
):
    """
    Get the current student's resume analysis with AI insights.
    """
    resume = db.query(Resume).filter(Resume.user_id == current_user.id).first()
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No resume found for this user"
        )
    
    analysis = db.query(ResumeAnalysis).filter(ResumeAnalysis.resume_id == resume.id).first()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No analysis found for this resume"
        )
    
    return analysis

@router.get("/analysis/{resume_id}", response_model=ResumeAnalysisResponse)
async def get_resume_analysis(
    resume_id: int,
    db: Session = Depends(get_db)
):
    """
    Get analysis for a specific resume (staff endpoint).
    """
    analysis = db.query(ResumeAnalysis).filter(ResumeAnalysis.resume_id == resume_id).first()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found for this resume"
        )
    
    return analysis

@router.post("/analysis/{resume_id}/improvement-plan")
async def get_resume_improvement_plan(
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_student_user)
):
    """
    Generate or retrieve improvement plan for student's resume.
    """
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user.id
    ).first()
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    analysis = db.query(ResumeAnalysis).filter(ResumeAnalysis.resume_id == resume_id).first()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No analysis found for this resume"
        )
    
    # Return existing or generate new improvement plan
    if analysis.improvement_plan:
        return {
            "improvement_plan": analysis.improvement_plan,
            "generated_at": analysis.updated_at
        }
    
    # Generate new improvement plan
    improvement_plan = await generate_improvement_plan(analysis.analysis_data)
    
    # Update database
    analysis.improvement_plan = improvement_plan
    db.commit()
    
    return {
        "improvement_plan": improvement_plan,
        "generated_at": analysis.updated_at
    }

@router.delete("/my-resume")
async def delete_my_resume(
    current_user: User = Depends(get_student_user),
    db: Session = Depends(get_db)
):
    """
    Delete the current student's resume and analysis.
    """
    resume = db.query(Resume).filter(Resume.user_id == current_user.id).first()
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No resume found"
        )
    
    # Delete analysis records
    analyses = db.query(ResumeAnalysis).filter(ResumeAnalysis.resume_id == resume.id).all()
    for analysis in analyses:
        db.delete(analysis)
    
    # Delete resume
    db.delete(resume)
    db.commit()
    
    return {"message": "Resume and analysis deleted successfully"}


@router.post("/search")
async def search_resumes(
    request: ResumeSearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Search resumes using semantic search.
    Staff can search all resumes, students can only search their own.
    """
    vector_store = get_vector_store()
    
    # Search in vector store
    results = await vector_store.search_resumes(
        query=request.query,
        top_k=request.top_k
    )
    
    # Filter results based on user role (staff can see all, students can only see their own)
    if current_user.role == "student":
        results = [r for r in results if r["metadata"]["user_id"] == str(current_user.id)]
    
    return {
        "query": request.query,
        "results": results,
        "count": len(results)
    }

