# Google Gemini Resume Analysis System

## Overview
A comprehensive AI-powered resume analysis system that uses Google Gemini to analyze student resumes, extract structured information, generate recommendations, and store analysis in a vector database for semantic search.

## Features

### 1. **Resume Analysis with Gemini AI**
- **Intelligent Parsing**: Uses Gemini to understand and extract key information from resume text
- **Structured Output**: Returns JSON with parsed:
  - Candidate name, email, phone
  - Professional summary
  - Skills (technical & soft skills)
  - Work experience with descriptions
  - Education details
  - Projects and accomplishments
  - Certifications and languages
  - Overall assessment and suitability score (0-100)

### 2. **Smart Recommendations**
- Generates 3-5 specific, actionable recommendations to improve resume
- Prioritizes recommendations (high/medium/low)
- Based on analysis of strengths and areas for improvement

### 3. **Improvement Plan Generation**
- Creates a personalized 30-60-90 day improvement plan
- Suggests skills to develop
- Recommends certifications to pursue
- Identifies projects to build
- Provides interview focus areas

### 4. **Vector Database Integration**
- Stores resume content and analysis in vector database
- Supports both ChromaDB and FAISS backends
- Enables semantic search across all processed resumes
- Chunks analysis data for better search granularity

## Architecture

### Services

#### `resume_analysis_service.py`
Main service for Gemini-based analysis:
- `ResumeAnalysisService.analyze_resume()` - Analyzes resume with Gemini
- `ResumeAnalysisService.store_analysis_in_vector_db()` - Stores in vector DB
- `ResumeAnalysisService.generate_improvement_plan()` - Creates improvement plan

#### `resume_service.py` (Updated)
Enhanced with:
- `process_resume()` - Extracts text from PDF and creates embeddings
- `analyze_resume_with_gemini()` - Orchestrates analysis workflow
- `generate_improvement_plan()` - Generates improvement plan

#### `vector_service.py`
Existing Google Generative AI embeddings integration:
- Uses `GoogleGenerativeAIEmbeddings` for embeddings
- FAISS for vector storage
- Semantic search capabilities

### Database Models

#### `Resume` (Existing)
```python
- id: Integer (Primary Key)
- user_id: Integer (Foreign Key)
- file_path: String
- file_name: String
- vector_store_id: String
- content_text: Text
- created_at, updated_at: DateTime
```

#### `ResumeAnalysis` (New)
```python
- id: Integer (Primary Key)
- resume_id: Integer (Foreign Key)
- user_id: Integer (Foreign Key)
- analysis_data: JSON (Gemini analysis output)
- recommendations: JSON (Improvement recommendations)
- improvement_plan: JSON (30-60-90 day plan)
- analysis_status: String (pending/completed/failed)
- vector_chunks_count: Integer
- suitability_score: Integer (0-100)
- created_at, updated_at: DateTime
```

### API Endpoints

#### Resume Upload (Enhanced)
**POST** `/resume/upload`
- Uploads PDF resume
- Automatically analyzes with Gemini
- Stores in vector database
- Generates recommendations and improvement plan
- Returns analysis ID and suitability score

**Response Example:**
```json
{
  "message": "Resume uploaded and analyzed successfully",
  "resume_id": 1,
  "analysis_id": 1,
  "file_name": "resume.pdf",
  "analysis_status": "completed",
  "suitability_score": 85,
  "vector_chunks_count": 12
}
```

#### Get Resume Analysis
**GET** `/resume/analysis/my-analysis`
- Returns current user's resume analysis
- Includes structured data from Gemini
- Shows suitability score and recommendations

#### Get Analysis Details
**GET** `/resume/analysis/{resume_id}`
- Retrieves analysis for specific resume
- Available to staff users

#### Generate/Get Improvement Plan
**POST** `/resume/analysis/{resume_id}/improvement-plan`
- Returns or generates improvement plan
- Creates 30-60-90 day actionable plan
- Recommends skills and certifications

#### Delete Resume & Analysis
**DELETE** `/resume/my-resume`
- Removes resume and all associated analysis
- Cleans up vector database entries

## Configuration

### Environment Variables (in `.env`)
```env
# Gemini API Configuration
GOOGLE_API_KEY=AIzaSyBoCB2mXwpdICcciZcGa3IIm_BHt2Zx9hg
LANGCHAIN_API_KEY=your-langchain-api-key

# Vector Store Configuration
VECTOR_STORE_TYPE=chromadb  # or faiss
VECTOR_STORE_PATH=./vector_store

# Database Configuration
DATABASE_URL=postgresql://postgres:Welcome%402025@localhost:5432/academic_analyser
```

### Settings (`app/config/settings.py`)
```python
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
VECTOR_STORE_TYPE = os.getenv("VECTOR_STORE_TYPE", "chromadb")
VECTOR_STORE_PATH = os.getenv("VECTOR_STORE_PATH", "./vector_store")
```

## Usage Flow

### 1. Student Uploads Resume
```
1. Student uploads PDF resume
2. System extracts text from PDF
3. Text is chunked and embedded for vector DB
4. Resume record created in database
```

### 2. Automatic Analysis
```
1. Gemini analyzes extracted resume text
2. Returns structured JSON with:
   - Skills and experience
   - Assessment and score
   - Key achievements
3. Recommendations generated
4. Analysis stored in ResumeAnalysis table
5. Analysis data stored in vector DB
```

### 3. Generate Improvement Plan
```
1. Staff/student requests improvement plan
2. System generates 30-60-90 day plan
3. Identifies skills gaps
4. Recommends certifications
5. Suggests projects to build
6. Plan saved in database
```

### 4. Semantic Search
```
1. Staff can search resumes by query
2. Vector DB returns semantically similar resumes
3. Used for matching students to opportunities
```

## Data Flow Diagram

```
Resume Upload
     ↓
PDF Text Extraction
     ↓
Vector DB Storage + Gemini Analysis
     ↓
├─ Structured Analysis (JSON)
├─ Recommendations
└─ Improvement Plan
     ↓
Database Storage
     ↓
API Response to Frontend
```

## Example Analysis Output

```json
{
  "candidate_name": "John Doe",
  "email": "john@example.com",
  "skills": ["Python", "JavaScript", "React", "SQL"],
  "technical_skills": ["Python", "Node.js", "MongoDB"],
  "soft_skills": ["Communication", "Leadership", "Problem Solving"],
  "experience": [
    {
      "position": "Software Engineer",
      "company": "Tech Corp",
      "duration": "2 years",
      "description": "Developed backend services..."
    }
  ],
  "suitability_score": 82,
  "overall_assessment": "Strong technical background...",
  "recommended_roles": ["Backend Developer", "Full Stack Developer"]
}
```

## Key Technologies

- **Google Gemini AI**: For intelligent resume analysis
- **Google Generative AI Embeddings**: For vectorization
- **LangChain**: Text splitting and vector operations
- **ChromaDB/FAISS**: Vector database storage
- **SQLAlchemy**: Database ORM
- **FastAPI**: REST API framework
- **Pydantic**: Data validation

## Performance Notes

- Analysis typically takes 5-15 seconds depending on resume length
- Vector DB queries return results in <100ms
- Recommendation generation takes 3-5 seconds
- Improvement plan generation takes 5-10 seconds

## Error Handling

- Failed analyses are marked with `analysis_status: "failed"`
- Error messages stored in database for debugging
- Fallback to raw response if JSON parsing fails
- Graceful degradation for missing analysis fields

## Future Enhancements

- [ ] Batch analysis for multiple resumes
- [ ] Real-time analysis progress updates via WebSockets
- [ ] Integration with job descriptions for matching
- [ ] Skill proficiency level assessment
- [ ] Resume template suggestions
- [ ] Comparison with industry standards
- [ ] Mock interview generation based on resume
- [ ] Plagiarism detection
- [ ] ATS score prediction

## Dependencies

Add to `requirements.txt`:
```
google-generativeai>=0.3.0
langchain>=0.1.0
chromadb>=0.4.0
faiss-cpu>=1.7.0  # or faiss-gpu for GPU support
pdfplumber>=0.10.0
```

## Testing

### Test Resume Analysis
```bash
curl -X POST http://localhost:8000/resume/upload \
  -F "file=@sample_resume.pdf" \
  -H "Authorization: Bearer <student_token>"
```

### Retrieve Analysis
```bash
curl http://localhost:8000/resume/analysis/my-analysis \
  -H "Authorization: Bearer <student_token>"
```

### Generate Improvement Plan
```bash
curl -X POST http://localhost:8000/resume/analysis/1/improvement-plan \
  -H "Authorization: Bearer <student_token>"
```

## Troubleshooting

### API Key Issues
- Verify `GOOGLE_API_KEY` is set in `.env`
- Check API key has Gemini API enabled
- Verify key has appropriate permissions

### Vector DB Issues
- Check `VECTOR_STORE_PATH` directory exists
- Verify ChromaDB/FAISS installation
- Check disk space for vector store

### Analysis Failures
- Check resume PDF is readable
- Verify resume has text (not image-only)
- Check Gemini API rate limits
- Review error message in `analysis_status`

## Security Considerations

- API keys stored in `.env` (never commit)
- Analysis restricted to authenticated users
- Students can only access their own analysis
- Staff can view all student analysis
- Vector DB access controlled via API authentication
