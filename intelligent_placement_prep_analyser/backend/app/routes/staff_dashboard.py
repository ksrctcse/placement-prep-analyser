"""
Staff Dashboard Routes
"""
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Header, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database.db import SessionLocal
from app.database.models import StaffProfile, Topic, Test, TestAttempt, User, UserRole
from app.services.pdf_service import process_pdf_for_rag
from app.services.vector_service import add_text_chunks, search_topic, delete_topic_store
from datetime import datetime
import os
from typing import Optional
from jose import JWTError, jwt

router = APIRouter(prefix="/staff", tags=["staff"])

# Configuration
UPLOAD_DIR = "uploads/topics"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {"pdf"}
SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
ALGORITHM = "HS256"


# Helper function to get current user from token
def get_current_user(token: str = None) -> dict:
    """Extract user info from JWT token"""
    if not token:
        raise HTTPException(status_code=401, detail="No token provided")
    
    try:
        # Extract token from Bearer scheme if present
        if token.startswith("Bearer "):
            token = token[7:]
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        role = payload.get("role")
        
        if not user_id or role != "staff":
            raise HTTPException(status_code=403, detail="Not authorized")
        
        return {"user_id": user_id, "role": role}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


class TopicCreate(BaseModel):
    title: str
    description: Optional[str] = None


class TopicResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    file_size: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class DashboardMetrics(BaseModel):
    total_topics: int
    total_tests: int
    total_students: int
    avg_student_score: float
    recent_tests: list


@router.get("/dashboard", response_model=dict)
async def get_dashboard(authorization: Optional[str] = Header(None)):
    """
    Get staff dashboard metrics (optimized)
    """
    db = SessionLocal()
    try:
        # Get staff ID from token
        if not authorization:
            raise HTTPException(status_code=401, detail="No authorization token")
        
        user_info = get_current_user(authorization)
        staff_user_id = user_info["user_id"]
        
        # Get staff profile with eager loading
        from sqlalchemy.orm import joinedload
        staff = db.query(StaffProfile).options(
            joinedload(StaffProfile.department)
        ).filter(
            StaffProfile.user_id == staff_user_id
        ).first()
        
        if not staff:
            raise HTTPException(status_code=404, detail="Staff profile not found")
        
        # Use aggregation queries for metrics (single trip to DB)
        from sqlalchemy import func
        from app.database.models import StudentProfile
        
        # Get all metrics in optimized way
        metrics = db.query(
            func.count(Topic.id).label('total_topics'),
            func.count(Test.id).label('total_tests'),
            func.avg(TestAttempt.score).label('avg_score')
        ).outerjoin(
            Test, Topic.id == Test.topic_id
        ).outerjoin(
            TestAttempt, Test.id == TestAttempt.test_id
        ).filter(
            Topic.staff_id == staff.id
        ).first()
        
        total_topics = metrics.total_topics or 0
        total_tests = metrics.total_tests or 0
        avg_score = round(float(metrics.avg_score) if metrics.avg_score else 0, 2)
        
        # Get students count
        total_students = db.query(func.count(StudentProfile.id)).filter(
            StudentProfile.department_id == staff.department_id
        ).scalar() or 0
        
        # Get recent tests with eager loading (limit 5)
        recent = db.query(TestAttempt).join(
            Test, TestAttempt.test_id == Test.id
        ).filter(
            Test.staff_id == staff.id
        ).order_by(TestAttempt.created_at.desc()).limit(5).all()
        
        recent_tests = [
            {
                "id": t.id,
                "test_title": t.test.title,
                "score": t.score,
                "created_at": t.created_at.isoformat()
            }
            for t in recent
        ]
        
        return {
            "total_topics": total_topics,
            "total_tests": total_tests,
            "total_students": total_students,
            "avg_student_score": avg_score,
            "recent_tests": recent_tests,
            "staff_name": staff.name,
            "department": staff.department.name
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/topics", response_model=list)
async def get_staff_topics(
    authorization: Optional[str] = Header(None),
    skip: int = 0,
    limit: int = 20
):
    """
    Get topics created by staff member (with pagination)
    """
    db = SessionLocal()
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="No authorization token")
        
        user_info = get_current_user(authorization)
        staff_user_id = user_info["user_id"]
        
        staff = db.query(StaffProfile).filter(
            StaffProfile.user_id == staff_user_id
        ).first()
        
        if not staff:
            raise HTTPException(status_code=404, detail="Staff profile not found")
        
        # Paginated query with limit
        topics = db.query(Topic).filter(
            Topic.staff_id == staff.id
        ).order_by(
            Topic.created_at.desc()
        ).offset(skip).limit(limit).all()
        
        return [
            {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "file_size": t.file_size,
                "is_indexed": t.is_indexed,
                "embedding_chunks": t.embedding_chunks,
                "created_at": t.created_at.isoformat(),
                "file_path": t.file_path
            }
            for t in topics
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.delete("/topics/{topic_id}")
async def delete_topic(
    topic_id: int,
    authorization: Optional[str] = Header(None)
):
    """
    Delete a topic by ID (deletes from database and vector store)
    Only the topic creator (staff) can delete it
    """
    db = SessionLocal()
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="No authorization token")
        
        user_info = get_current_user(authorization)
        staff_user_id = user_info["user_id"]
        
        # Get staff profile
        staff = db.query(StaffProfile).filter(
            StaffProfile.user_id == staff_user_id
        ).first()
        
        if not staff:
            raise HTTPException(status_code=404, detail="Staff profile not found")
        
        # Get topic
        topic = db.query(Topic).filter(Topic.id == topic_id).first()
        
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")
        
        # Verify ownership
        if topic.staff_id != staff.id:
            raise HTTPException(
                status_code=403,
                detail="You can only delete your own topics"
            )
        
        # Delete vector store embeddings
        try:
            delete_topic_store(topic_id)
            print(f"✓ Vector store deleted for topic {topic_id}")
        except Exception as e:
            print(f"⚠️  Failed to delete vector store: {e}")
            # Continue with database deletion even if vector store deletion fails
        
        # Delete uploaded PDF file if it exists
        if topic.file_path and os.path.exists(topic.file_path):
            try:
                os.remove(topic.file_path)
                print(f"✓ PDF file deleted: {topic.file_path}")
            except Exception as e:
                print(f"⚠️  Failed to delete PDF file: {e}")
                # Continue with database deletion even if file deletion fails
        
        # Delete from database
        db.delete(topic)
        db.commit()
        
        return {
            "message": f"Topic '{topic.title}' deleted successfully",
            "topic_id": topic_id
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ Error deleting topic: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/upload-topic")
async def upload_topic(
    title: str = Form(...),
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    authorization: Optional[str] = Header(None)
):
    """
    Upload a PDF topic with 10MB limit and RAG processing
    - Extracts text from PDF
    - Creates chunks
    - Generates embeddings and stores in vector database
    """
    db = SessionLocal()
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="No authorization token")
        
        user_info = get_current_user(authorization)
        staff_user_id = user_info["user_id"]
        
        # Get staff profile
        staff = db.query(StaffProfile).filter(
            StaffProfile.user_id == staff_user_id
        ).first()
        
        if not staff:
            raise HTTPException(status_code=404, detail="Staff profile not found")
        
        # Validate file
        if not file.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files allowed")
        
        # Read file content to check size
        content = await file.read()
        file_size = len(content)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File size exceeds 10MB limit. Current size: {file_size / 1024 / 1024:.2f}MB"
            )
        
        # Create upload directory if it doesn't exist
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        
        # Save file
        file_path = os.path.join(UPLOAD_DIR, f"{staff.id}_{datetime.now().timestamp()}_{file.filename}")
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Create topic record (will update with embedding stats after processing)
        topic = Topic(
            title=title,
            description=description,
            file_path=file_path,
            file_size=file_size,
            staff_id=staff.id,
            is_indexed=False,
            embedding_chunks=0
        )
        db.add(topic)
        db.commit()
        db.refresh(topic)
        
        # Process PDF for RAG (extract text and create embeddings)
        try:
            print(f"\n📋 Starting RAG processing for topic: {title}")
            print(f"   File path: {file_path}")
            chunks, metadatas = process_pdf_for_rag(file_path)
            print(f"✓ PDF processing complete: {len(chunks)} chunks extracted")
            
            # Add chunks to vector store
            print(f"📤 Adding chunks to vector store...")
            num_chunks = add_text_chunks(topic.id, chunks, metadatas)
            print(f"✓ Vector store updated: {num_chunks} chunks")
            
            # Update topic with embedding information
            topic.is_indexed = True
            topic.embedding_chunks = num_chunks
            topic.last_indexed_at = datetime.utcnow()
            db.commit()
            db.refresh(topic)
            
            print(f"✓ Topic {topic.id} indexed successfully with {num_chunks} chunks\n")
            
            return {
                "id": topic.id,
                "title": topic.title,
                "description": topic.description,
                "file_size": topic.file_size,
                "is_indexed": topic.is_indexed,
                "embedding_chunks": topic.embedding_chunks,
                "created_at": topic.created_at.isoformat(),
                "message": f"Topic uploaded successfully! Processed {num_chunks} chunks for semantic search."
            }
        except Exception as rag_error:
            # If RAG processing fails, still keep the topic but mark as not indexed
            print(f"\n⚠️  RAG processing error: {type(rag_error).__name__}: {rag_error}")
            print(f"   Reason: Check if GOOGLE_API_KEY environment variable is set")
            print(f"   The topic will still be saved but without semantic search indexing\n")
            
            topic.is_indexed = False
            topic.embedding_chunks = 0
            db.commit()
            
            return {
                "id": topic.id,
                "title": topic.title,
                "description": topic.description,
                "file_size": topic.file_size,
                "is_indexed": False,
                "embedding_chunks": 0,
                "created_at": topic.created_at.isoformat(),
                "message": "Topic uploaded but semantic indexing failed. Basic retrieval still available.",
                "warning": str(rag_error)
            }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/topics/{topic_id}/reindex")
async def reindex_topic(
    topic_id: int,
    authorization: Optional[str] = Header(None)
):
    """
    Retry semantic indexing for a topic that failed to index
    """
    db = SessionLocal()
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="No authorization token")
        
        user_info = get_current_user(authorization)
        staff_user_id = user_info["user_id"]
        
        # Get staff profile
        staff = db.query(StaffProfile).filter(
            StaffProfile.user_id == staff_user_id
        ).first()
        
        if not staff:
            raise HTTPException(status_code=404, detail="Staff profile not found")
        
        # Get topic
        topic = db.query(Topic).filter(Topic.id == topic_id).first()
        
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")
        
        # Verify ownership
        if topic.staff_id != staff.id:
            raise HTTPException(
                status_code=403,
                detail="You can only re-index your own topics"
            )
        
        # Check if file exists
        if not os.path.exists(topic.file_path):
            raise HTTPException(
                status_code=400,
                detail="PDF file not found. Please re-upload the topic."
            )
        
        print(f"\n🔄 Re-indexing topic {topic_id}: {topic.title}")
        print(f"   File path: {topic.file_path}")
        
        # Process PDF for RAG
        try:
            chunks, metadatas = process_pdf_for_rag(topic.file_path)
            print(f"✓ PDF processing complete: {len(chunks)} chunks extracted")
            
            # Clear old vector store if it exists
            try:
                delete_topic_store(topic_id)
                print(f"✓ Old vector store cleared")
            except:
                pass  # It's okay if old store doesn't exist
            
            # Add chunks to vector store
            print(f"📤 Adding chunks to vector store...")
            num_chunks = add_text_chunks(topic.id, chunks, metadatas)
            print(f"✓ Vector store updated: {num_chunks} chunks")
            
            # Update topic with embedding information
            topic.is_indexed = True
            topic.embedding_chunks = num_chunks
            topic.last_indexed_at = datetime.utcnow()
            db.commit()
            db.refresh(topic)
            
            print(f"✓ Topic {topic.id} re-indexed successfully with {num_chunks} chunks\n")
            
            return {
                "id": topic.id,
                "title": topic.title,
                "is_indexed": topic.is_indexed,
                "embedding_chunks": topic.embedding_chunks,
                "message": f"Topic re-indexed successfully! Processed {num_chunks} chunks for semantic search.",
                "updated_at": topic.last_indexed_at.isoformat()
            }
        except Exception as rag_error:
            print(f"\n⚠️  Re-indexing error: {type(rag_error).__name__}: {rag_error}")
            db.rollback()
            raise HTTPException(
                status_code=400,
                detail=f"Failed to re-index topic: {str(rag_error)}"
            )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ Error re-indexing topic: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/search-topic/{topic_id}")
async def search_topic_content(
    topic_id: int,
    query: str,
    authorization: Optional[str] = Header(None)
):
    """
    Search within a specific topic using RAG/semantic similarity
    Returns relevant text chunks from the topic's PDF
    """
    db = SessionLocal()
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="No authorization token")
        
        user_info = get_current_user(authorization)
        
        # Get topic and verify it exists
        topic = db.query(Topic).filter(Topic.id == topic_id).first()
        
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")
        
        if not topic.is_indexed:
            raise HTTPException(
                status_code=400, 
                detail="This topic has not been indexed for semantic search yet. Please wait while indexing completes."
            )
        
        if not query or not query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Perform semantic search within the topic
        results = search_topic(topic_id, query, k=5)
        
        return {
            "topic_id": topic_id,
            "topic_title": topic.title,
            "query": query,
            "results": results,
            "num_results": len(results)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/performance-metrics")
async def get_performance_metrics(authorization: Optional[str] = Header(None)):
    """
    Get student performance metrics for topics created by staff
    """
    db = SessionLocal()
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="No authorization token")
        
        user_info = get_current_user(authorization)
        staff_user_id = user_info["user_id"]
        
        staff = db.query(StaffProfile).filter(
            StaffProfile.user_id == staff_user_id
        ).first()
        
        if not staff:
            raise HTTPException(status_code=404, detail="Staff profile not found")
        
        # Use database aggregations for metrics (single efficient query)
        from sqlalchemy import func, case
        from app.database.models import StudentProfile as SP
        
        status_metrics = db.query(
            func.count(TestAttempt.id).label('total_attempts'),
            func.sum(case((TestAttempt.status == "completed", 1), else_=0)).label('completed'),
            func.sum(case((TestAttempt.status == "in_progress", 1), else_=0)).label('in_progress'),
            func.sum(case((TestAttempt.status == "pending", 1), else_=0)).label('pending'),
            func.avg(TestAttempt.score).label('average_score')
        ).join(
            Test,
            TestAttempt.test_id == Test.id
        ).filter(
            Test.staff_id == staff.id
        ).first()
        
        metrics = {
            "total_attempts": status_metrics.total_attempts or 0,
            "completed": status_metrics.completed or 0,
            "in_progress": status_metrics.in_progress or 0,
            "pending": status_metrics.pending or 0,
            "average_score": round(float(status_metrics.average_score) if status_metrics.average_score else 0, 2),
            "top_performers": []
        }
        
        # Get top performers (limit 5)
        from sqlalchemy import func
        top_performers = db.query(
            TestAttempt.student_id,
            SP.name,
            func.avg(TestAttempt.score).label("avg_score")
        ).join(
            SP,
            TestAttempt.student_id == SP.id
        ).join(
            Test,
            TestAttempt.test_id == Test.id
        ).filter(
            Test.staff_id == staff.id,
            TestAttempt.score.isnot(None)
        ).group_by(
            TestAttempt.student_id, SP.name
        ).order_by(func.avg(TestAttempt.score).desc()).limit(5).all()
        
        metrics["top_performers"] = [
            {"student_id": p[0], "name": p[1], "avg_score": round(float(p[2]), 2)}
            for p in top_performers
        ]
        
        return metrics
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
