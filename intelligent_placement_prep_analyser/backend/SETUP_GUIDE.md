# Backend Setup & Quick Start Guide

## Project Overview
This is a FastAPI-based backend for the Placement Prep Analyser with:
- User authentication (Student & Staff)
- JWT-based authorization
- Resume management with vector storage
- AI-powered interview prep
- Role-based access control

---

## Quick Setup (5 minutes)

### Step 1: Navigate to Backend Directory
```bash
cd intelligent_placement_prep_analyser/backend
```

### Step 2: Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Setup Environment Variables
```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your Gemini API key
# GEMINI_API_KEY=your_actual_api_key_here
```

### Step 5: Initialize Database
```bash
python -m app.database.init_db
```

### Step 6: Start the Server
```bash
uvicorn app.main:app --reload
```

The API will be available at: **http://localhost:8000**
- API Documentation: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

---

## Testing the API

### Using curl

#### 1. Student Signup
```bash
curl -X POST "http://localhost:8000/auth/student/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "password": "password123",
    "department": "CSE",
    "batch": "2024-2027"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer",
  "user_id": 1,
  "role": "student",
  "name": "John Doe"
}
```

#### 2. Staff Signup
```bash
curl -X POST "http://localhost:8000/auth/staff/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Dr. Jane Smith",
    "email": "jane@example.com",
    "password": "password123",
    "staff_id": "STAFF001",
    "position": "Assistant Professor"
  }'
```

#### 3. Login
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "password123"
  }'
```

#### 4. Get Current User (Protected Endpoint)
```bash
curl -X GET "http://localhost:8000/auth/me" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

#### 5. Get Student Dashboard
```bash
curl -X GET "http://localhost:8000/student/dashboard" \
  -H "Authorization: Bearer YOUR_STUDENT_TOKEN"
```

#### 6. Upload Resume
```bash
curl -X POST "http://localhost:8000/resume/upload" \
  -H "Authorization: Bearer YOUR_STUDENT_TOKEN" \
  -F "file=@path/to/resume.pdf"
```

#### 7. Get Interview Question
```bash
curl -X GET "http://localhost:8000/interview/question" \
  -H "Authorization: Bearer YOUR_STUDENT_TOKEN"
```

#### 8. Evaluate Answer
```bash
curl -X POST "http://localhost:8000/interview/evaluate" \
  -H "Authorization: Bearer YOUR_STUDENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is REST API?",
    "answer": "REST API is a web service that uses HTTP methods...",
    "question_type": "technical"
  }'
```

---

### Using Postman

1. Import the API by URL:
   - `http://localhost:8000/openapi.json`

2. Or manually create requests:
   - **Method**: POST
   - **URL**: http://localhost:8000/auth/student/signup
   - **Body** (JSON):
   ```json
   {
     "name": "John Doe",
     "email": "john@test.com",
     "password": "password123",
     "department": "CSE",
     "batch": "2024-2027"
   }
   ```

3. For protected endpoints, add Authorization header:
   - **Type**: Bearer Token
   - **Token**: [Your JWT token from login response]

---

### Using Python Requests

Create a `test_api.py` file:

```python
import requests
import json

BASE_URL = "http://localhost:8000"

# Test 1: Student Signup
print("=== Student Signup ===")
response = requests.post(
    f"{BASE_URL}/auth/student/signup",
    json={
        "name": "John Doe",
        "email": "john@example.com",
        "password": "password123",
        "department": "CSE",
        "batch": "2024-2027"
    }
)
print(response.json())
student_token = response.json().get("access_token")

# Test 2: Staff Signup
print("\n=== Staff Signup ===")
response = requests.post(
    f"{BASE_URL}/auth/staff/signup",
    json={
        "name": "Dr. Jane Smith",
        "email": "jane@example.com",
        "password": "password123",
        "staff_id": "STAFF001",
        "position": "Assistant Professor"
    }
)
print(response.json())
staff_token = response.json().get("access_token")

# Test 3: Get Student Dashboard
print("\n=== Student Dashboard ===")
response = requests.get(
    f"{BASE_URL}/student/dashboard",
    headers={"Authorization": f"Bearer {student_token}"}
)
print(response.json())

# Test 4: Get Interview Question
print("\n=== Interview Question ===")
response = requests.get(
    f"{BASE_URL}/interview/question",
    headers={"Authorization": f"Bearer {student_token}"}
)
print(response.json())

# Test 5: Evaluate Answer
print("\n=== Evaluate Answer ===")
response = requests.post(
    f"{BASE_URL}/interview/evaluate",
    headers={"Authorization": f"Bearer {student_token}"},
    json={
        "question": "What is Python?",
        "answer": "Python is a high-level programming language...",
        "question_type": "general"
    }
)
print(response.json())

# Test 6: Get Staff Dashboard
print("\n=== Staff Dashboard ===")
response = requests.get(
    f"{BASE_URL}/staff/dashboard",
    headers={"Authorization": f"Bearer {staff_token}"}
)
print(response.json())
```

Run the test:
```bash
python test_api.py
```

---

## Available Departments & Batches

### Departments:
- CSE (Computer Science Engineering)
- IT (Information Technology)
- EEE (Electrical and Electronics Engineering)
- ECE (Electronics and Communication Engineering)
- MECH (Mechanical Engineering)
- CIVL (Civil Engineering)
- CSBS (Cyber Security & Block Chain)

### Batches:
- 2024-2027
- 2025-2028

---

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── auth/
│   │   ├── jwt_handler.py      # JWT token creation & verification
│   │   ├── dependencies.py     # Auth dependencies for route protection
│   │   └── __init__.py
│   ├── config/
│   │   ├── settings.py         # Configuration management
│   │   └── __init__.py
│   ├── database/
│   │   ├── db.py               # Database initialization
│   │   ├── models.py           # SQLAlchemy models
│   │   ├── init_db.py          # Database table creation
│   │   └── __init__.py
│   ├── routes/
│   │   ├── auth_routes.py      # Authentication endpoints
│   │   ├── student_routes.py   # Student-specific endpoints
│   │   ├── staff_routes.py     # Staff-specific endpoints
│   │   ├── resume_routes.py    # Resume management endpoints
│   │   ├── interview_routes.py # Interview endpoints
│   │   └── __init__.py
│   └── services/
│       ├── gemini_service.py   # Gemini API integration
│       ├── interview_service.py # Interview logic
│       ├── resume_service.py   # Resume processing
│       ├── vector_store_service.py # Vector embeddings
│       └── __init__.py
├── requirements.txt            # Python dependencies
├── .env.example               # Environment template
├── API_DOCUMENTATION.md       # Complete API docs
├── SETUP_GUIDE.md            # This file
└── placement.db              # SQLite database (created after init)
```

---

## Common Issues & Solutions

### Issue: `ModuleNotFoundError: No module named 'app'`
**Solution**: Make sure you're running from the backend directory and using the correct Python path.
```bash
cd intelligent_placement_prep_analyser/backend
python -m app.database.init_db
```

### Issue: `GEMINI_API_KEY not found`
**Solution**: Create .env file with your Gemini API key:
```bash
echo "GEMINI_API_KEY=your_key_here" >> .env
```

### Issue: `Database is locked` (SQLite)
**Solution**: This happens when multiple processes access SQLite. For production, use PostgreSQL:
```
DATABASE_URL=postgresql://user:password@localhost:5432/placement_db
```

### Issue: `Port 8000 already in use`
**Solution**: Use a different port:
```bash
uvicorn app.main:app --reload --port 8001
```

### Issue: CORS errors when accessing from frontend
**Solution**: Update `ALLOW_ORIGINS` in `.env`:
```
ALLOW_ORIGINS=http://localhost:3000,http://localhost:3001
```

---

## Debugging

### Enable Debug Logging
Edit `.env`:
```
DEBUG=True
LOG_LEVEL=DEBUG
```

### View Database Contents
```python
from app.database.db import SessionLocal, Base
from app.database.models import User, Resume, InterviewReport

db = SessionLocal()
users = db.query(User).all()
for user in users:
    print(f"{user.id}: {user.name} ({user.role.value})")
```

### Test Database Connection
```python
from app.database.db import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text("SELECT 1"))
    print("Database connection successful!")
```

---

## Database Migrations (Optional - Using Alembic)

For production, use Alembic for migrations:

```bash
# Install Alembic
pip install alembic

# Initialize Alembic
alembic init migrations

# Create a migration
alembic revision --autogenerate -m "Add new column"

# Apply migrations
alembic upgrade head
```

---

## Performance Tips

1. **Use PostgreSQL** instead of SQLite for production
2. **Index frequently queried columns** (already done for `email`, `user_id`)
3. **Use connection pooling** for database
4. **Cache vector store** for repeated searches
5. **Implement pagination** for large datasets
6. **Use async routes** for I/O operations

---

## Next Steps

1. ✅ Backend API setup complete
2. ⬜ Connect frontend to these API endpoints
3. ⬜ Add more interview questions and Gemini integration
4. ⬜ Implement resume parsing improvements
5. ⬜ Add email notifications
6. ⬜ Set up automated deployment

---

## Support & Documentation

- **Full API Documentation**: See `API_DOCUMENTATION.md`
- **FastAPI Docs**: http://localhost:8000/docs
- **Python-Jose**: https://pypi.org/project/python-jose/
- **SQLAlchemy**: https://docs.sqlalchemy.org/
- **Pydantic**: https://docs.pydantic.dev/

---

**Created**: March 27, 2024  
**Last Updated**: March 27, 2024  
**Maintained By**: Development Team
