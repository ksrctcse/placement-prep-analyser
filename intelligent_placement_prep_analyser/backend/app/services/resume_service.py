
import pdfplumber
import os
from io import BytesIO
from datetime import datetime
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.services.vector_service import add_chunks
from app.services.resume_analysis_service import resume_analysis

async def process_resume(file):
    """
    Process resume PDF: extract text, analyze with Gemini, and store in vector DB.
    
    Args:
        file: Uploaded file object
    
    Returns:
        Dictionary with processing results
    """
    text = ""
    # Read file content
    file_content = await file.read()
    
    # Extract text from PDF
    with pdfplumber.open(BytesIO(file_content)) as pdf:
        for p in pdf.pages:
            text += p.extract_text()
    
    # Save file to disk
    uploads_dir = "./uploads"
    os.makedirs(uploads_dir, exist_ok=True)
    
    timestamp = datetime.utcnow().timestamp()
    file_path = os.path.join(uploads_dir, f"{timestamp}_{file.filename}")
    
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    # Process with vector embeddings
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_text(text)
    add_chunks(chunks)
    
    return {
        "text": text,
        "file_path": file_path,
        "chunk_count": len(chunks),
        "file_name": file.filename
    }

async def analyze_resume_with_gemini(resume_text: str, user_id: int, file_name: str):
    """
    Analyze resume using Gemini AI and store in vector database.
    
    Args:
        resume_text: Extracted text from resume
        user_id: User ID for tracking
        file_name: Original file name
    
    Returns:
        Dictionary containing analysis results and vector DB IDs
    """
    # Analyze with Gemini
    analysis_result = await resume_analysis.analyze_resume(resume_text, user_id, file_name)
    
    # Store analysis in vector DB
    if analysis_result.get("analysis_status") == "completed":
        vector_chunks = await resume_analysis.store_analysis_in_vector_db(
            resume_text,
            analysis_result,
            user_id
        )
        analysis_result["vector_chunks"] = vector_chunks
        analysis_result["vector_chunks_count"] = len(vector_chunks)
    
    return analysis_result

async def generate_improvement_plan(analysis_data: dict):
    """
    Generate a personalized improvement plan based on resume analysis.
    
    Args:
        analysis_data: Analysis data from Gemini
    
    Returns:
        Improvement plan
    """
    return await resume_analysis.generate_improvement_plan(analysis_data)

