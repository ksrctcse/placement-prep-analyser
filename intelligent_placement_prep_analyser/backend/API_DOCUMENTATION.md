# Placement Prep Analyser - Backend API Documentation

## Overview
This is a comprehensive backend API for a Placement Preparation Analyser with AI assistance. It supports separate authentication for students and staff, role-based access control, resume storage with vector embeddings, and interview preparation features.

## Features
- **Dual Authentication System**: Separate signup/login for Students and Staff
- **JWT Token-Based Authorization**: Secure API endpoints with token validation
- **Role-Based Access Control**: Different permissions for students, staff, and admins
- **Vector Store Integration**: ChromaDB/FAISS for semantic resume search
- **Interview Module**: AI-powered question generation and answer evaluation
- **Student Profiles**: Department and batch tracking
- **Staff Analytics**: Student progress tracking and feedback management

---

## Setup Instructions

### 1. Prerequisites
- Python 3.8+
- SQLite (default) or PostgreSQL
- Gemini API key

### 2. Installation

```bash
# Navigate to backend directory
cd intelligent_placement_prep_analyser/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with configuration
cat > .env << EOF
GEMINI_API_KEY=your_gemini_api_key_here
JWT_SECRET=your_secret_key_change_in_production
DATABASE_URL=sqlite:///placement.db
VECTOR_STORE_TYPE=chromadb
DEBUG=True
EOF

# Initialize database tables
python -m app.database.init_db

# Run the server
uvicorn app.main:app --reload
```

### 3. API Server
- The API will be available at: `http://localhost:8000`
- Interactive API docs: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`

---

## Authentication

### JWT Token Structure
All tokens include:
- `user_id`: User's unique identifier
- `role`: User role (student, staff, admin)
- `email`: User's email
- `exp`: Token expiration time (24 hours by default)
- `iat`: Token issue time

### Token Usage
Include token in request headers:
```
Authorization: Bearer <your_jwt_token>
```

---

## API Endpoints

### Authentication Endpoints (`/auth`)

#### Student Signup
```
POST /auth/student/signup
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "securepass123",
  "department": "CSE",
  "batch": "2024-2027"
}

Response:
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user_id": 1,
  "role": "student",
  "name": "John Doe"
}
```

**Valid Departments**: CSE, IT, EEE, ECE, MECH, CIVL, CSBS
**Valid Batches**: 2024-2027, 2025-2028

#### Staff Signup
```
POST /auth/staff/signup
Content-Type: application/json

{
  "name": "Dr. Jane Smith",
  "email": "jane@example.com",
  "password": "securepass123",
  "staff_id": "STAFF001",
  "position": "Assistant Professor"
}

Response:
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user_id": 2,
  "role": "staff",
  "name": "Dr. Jane Smith"
}
```

#### Login (Both Student and Staff)
```
POST /auth/login
Content-Type: application/json

{
  "email": "john@example.com",
  "password": "securepass123"
}

Response:
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user_id": 1,
  "role": "student",
  "name": "John Doe"
}
```

#### Get Current User Profile
```
GET /auth/me
Authorization: Bearer <token>

Response:
{
  "id": 1,
  "name": "John Doe",
  "email": "john@example.com",
  "role": "student",
  "department": "CSE",
  "batch": "2024-2027"
}
```

#### Get User Profile by ID
```
GET /auth/users/{user_id}

Response:
{
  "id": 1,
  "name": "John Doe",
  "email": "john@example.com",
  "role": "student",
  "department": "CSE",
  "batch": "2024-2027"
}
```

---

### Student Endpoints (`/student`)

#### Get Student Dashboard
```
GET /student/dashboard
Authorization: Bearer <student_token>

Response:
{
  "user_id": 1,
  "name": "John Doe",
  "email": "john@example.com",
  "department": "CSE",
  "batch": "2024-2027",
  "progress": "Good",
  "recommendations": [
    "Practice system design problems",
    "Review data structures",
    "Work on coding problems on LeetCode",
    "Prepare for behavioral interviews"
  ]
}
```

#### List All Students (Staff Only)
```
GET /student/list
Authorization: Bearer <staff_token>

Response:
{
  "total_students": 5,
  "students": [
    {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "department": "CSE",
      "batch": "2024-2027"
    }
  ]
}
```

#### Get Student Profile
```
GET /student/{student_id}
Authorization: Bearer <token>

Response:
{
  "id": 1,
  "name": "John Doe",
  "email": "john@example.com",
  "department": "CSE",
  "batch": "2024-2027",
  "created_at": "2024-03-27T10:00:00"
}
```

---

### Staff Endpoints (`/staff`)

#### Get Staff Dashboard
```
GET /staff/dashboard
Authorization: Bearer <staff_token>

Response:
{
  "staff_name": "Dr. Jane Smith",
  "position": "Assistant Professor",
  "total_students": 5,
  "total_staff": 2,
  "message": "Staff dashboard loaded successfully"
}
```

#### Get Students Progress
```
GET /staff/students-progress
Authorization: Bearer <staff_token>

Response:
{
  "total_students": 5,
  "students": [
    {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "department": "CSE",
      "batch": "2024-2027",
      "score": 8,
      "feedback": "Good performance on technical questions"
    }
  ]
}
```

#### Get Students by Department
```
GET /staff/students-by-department/{department}
Authorization: Bearer <staff_token>

Example: GET /staff/students-by-department/CSE

Response:
{
  "department": "CSE",
  "total_students": 3,
  "students": [
    {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "batch": "2024-2027"
    }
  ]
}
```

#### Add Interview Feedback
```
POST /staff/add-interview-feedback
Authorization: Bearer <staff_token>
Content-Type: application/json

{
  "student_id": 1,
  "score": 8,
  "feedback": "Excellent technical knowledge, needs improvement in communication",
  "interview_type": "technical"
}

Response:
{
  "message": "Feedback added successfully",
  "report_id": 1,
  "student_name": "John Doe",
  "score": 8
}
```

#### Get Student Interviews
```
GET /staff/interviews/{student_id}
Authorization: Bearer <staff_token>

Response:
{
  "student_name": "John Doe",
  "email": "john@example.com",
  "total_interviews": 3,
  "interviews": [
    {
      "id": 1,
      "score": 8,
      "feedback": "Excellent technical knowledge",
      "interview_type": "technical",
      "created_at": "2024-03-27T10:00:00"
    }
  ]
}
```

---

### Resume Endpoints (`/resume`)

#### Upload Resume
```
POST /resume/upload
Authorization: Bearer <student_token>
Content-Type: multipart/form-data

File: resume.pdf (binary file)

Response:
{
  "message": "Resume uploaded successfully",
  "resume_id": 1,
  "vector_store_id": "resume_1_1711604400",
  "file_name": "resume.pdf"
}
```

#### Get My Resume
```
GET /resume/my-resume
Authorization: Bearer <student_token>

Response:
{
  "id": 1,
  "user_id": 1,
  "file_name": "resume.pdf",
  "file_path": "/uploads/resume_1.pdf",
  "vector_store_id": "resume_1_1711604400",
  "created_at": "2024-03-27T10:00:00",
  "updated_at": "2024-03-27T10:00:00"
}
```

#### Get User Resume
```
GET /resume/{user_id}

Response:
{
  "id": 1,
  "user_id": 1,
  "file_name": "resume.pdf",
  "file_path": "/uploads/resume_1.pdf",
  "vector_store_id": "resume_1_1711604400",
  "created_at": "2024-03-27T10:00:00",
  "updated_at": "2024-03-27T10:00:00"
}
```

#### Delete Resume
```
DELETE /resume/my-resume
Authorization: Bearer <student_token>

Response:
{
  "message": "Resume deleted successfully"
}
```

#### Search Resumes
```
POST /resume/search
Authorization: Bearer <token>
Content-Type: application/json

{
  "query": "machine learning projects",
  "top_k": 5
}

Response:
{
  "query": "machine learning projects",
  "results": [
    {
      "vector_id": "resume_1_1711604400",
      "content": "Resume text content...",
      "metadata": {
        "user_id": "1",
        "file_name": "resume.pdf",
        "created_at": "2024-03-27T10:00:00"
      },
      "distance": 0.15
    }
  ],
  "count": 1
}
```

---

### Interview Endpoints (`/interview`)

#### Get Interview Question
```
GET /interview/question
Authorization: Bearer <student_token>

Response:
{
  "question": "What is the difference between REST and GraphQL?",
  "question_type": "general",
  "difficulty": "intermediate"
}
```

#### Evaluate Interview Answer
```
POST /interview/evaluate
Authorization: Bearer <student_token>
Content-Type: application/json

{
  "question": "What is the difference between REST and GraphQL?",
  "answer": "REST uses HTTP methods while GraphQL uses a query language...",
  "question_type": "technical"
}

Response:
{
  "feedback": "Good understanding of both concepts...",
  "score": 8,
  "improvements": [
    "Work on technical depth",
    "Provide more examples",
    "Practice similar questions"
  ]
}
```

#### Get Interview History
```
GET /interview/my-interview-history
Authorization: Bearer <student_token>

Response:
{
  "total_interviews": 5,
  "average_score": 7.8,
  "interviews": [
    {
      "id": 5,
      "score": 8,
      "feedback": "Excellent response...",
      "interview_type": "technical",
      "created_at": "2024-03-27T10:00:00"
    }
  ]
}
```

#### Get Interview Details
```
GET /interview/interview/{interview_id}
Authorization: Bearer <student_token>

Response:
{
  "id": 5,
  "score": 8,
  "feedback": "Excellent response...",
  "interview_type": "technical",
  "created_at": "2024-03-27T10:00:00"
}
```

---

## Database Schema

### Users Table
```sql
id (PRIMARY KEY)
name (String)
email (String, UNIQUE)
password (String, hashed)
role (Enum: student, staff, admin)
department (Enum: CSE, IT, EEE, ECE, MECH, CIVL, CSBS)
batch (Enum: 2024-2027, 2025-2028)
staff_id (String, UNIQUE, nullable)
position (String, nullable)
created_at (DateTime)
updated_at (DateTime)
```

### Resumes Table
```sql
id (PRIMARY KEY)
user_id (FOREIGN KEY -> users.id)
file_name (String)
file_path (String)
vector_store_id (String, nullable)
content_text (Text, nullable)
created_at (DateTime)
updated_at (DateTime)
```

### Interview Reports Table
```sql
id (PRIMARY KEY)
user_id (FOREIGN KEY -> users.id)
score (Integer)
feedback (String)
interview_type (String)
created_at (DateTime)
```

---

## Vector Store Configuration

### ChromaDB (Default)
- Persistent storage at `./vector_store`
- Uses cosine similarity for search
- Automatically manages embeddings

### FAISS
- Fast search for large-scale similarity search
- Stores metadata separately
- Better performance for thousands of documents

**To switch vector store**, update `.env`:
```
VECTOR_STORE_TYPE=faiss  # or chromadb
```

---

## Error Handling

All errors follow standard HTTP status codes:

```
200 OK - Successful request
201 Created - Resource created
400 Bad Request - Invalid input
401 Unauthorized - Missing or invalid token
403 Forbidden - Insufficient permissions
404 Not Found - Resource not found
500 Internal Server Error - Server error
```

Example error response:
```json
{
  "detail": "Invalid email or password"
}
```

---

## Security Considerations

1. **Password Hashing**: Uses bcrypt for secure password hashing
2. **JWT Tokens**: 24-hour expiration by default
3. **Role-Based Access**: Students can only access their own data
4. **CORS**: Configured for localhost development
5. **HTTPS**: Recommended for production deployment

---

## Production Deployment

### Before Deployment:

1. Update `.env` variables:
   ```
   JWT_SECRET=<long-random-string>
   DATABASE_URL=postgresql://<user>:<password>@<host>/<db>
   DEBUG=False
   ALLOW_ORIGINS=["https://yourdomain.com"]
   ```

2. Use production ASGI server:
   ```bash
   pip install gunicorn
   gunicorn app.main:app -w 4 -b 0.0.0.0:8000
   ```

3. Use PostgreSQL instead of SQLite

4. Enable HTTPS/SSL

5. Set up proper logging and monitoring

---

## Development Notes

- All timestamps are in UTC
- Emails are validated using Pydantic
- File uploads are stored in `./uploads/` directory
- Database migrations can be created using Alembic (optional)

---

## Support

For issues or questions, refer to the main README.md or contact the development team.
