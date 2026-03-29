# Placement Prep Analyser - Complete Setup Guide

## Project Structure

```
intelligent_placement_prep_analyser/
├── backend/
│   ├── venv/                          # Python virtual environment
│   ├── app/
│   │   ├── main.py                    # FastAPI app with CORS & Swagger
│   │   ├── config/
│   │   │   └── settings.py            # Configuration from .env
│   │   ├── database/
│   │   │   ├── db.py                  # PostgreSQL connection
│   │   │   ├── models.py              # SQLAlchemy models
│   │   │   └── migrate.py             # Migration script
│   │   ├── routes/                    # API endpoints
│   │   ├── services/                  # Business logic
│   │   └── auth/
│   ├── requirements.txt               # Python dependencies
│   ├── .env                           # Environment variables
│   └── app/database/migrate.py        # Run migrations
│
├── frontend/primereact-app/
│   ├── src/
│   │   ├── App.jsx                    # Main React component
│   │   ├── main.jsx                   # Entry point
│   │   ├── config/
│   │   │   └── api.js                 # API endpoints config
│   │   └── pages/
│   │       ├── StudentDashboard.jsx
│   │       └── StaffDashboard.jsx
│   ├── index.html                     # HTML template
│   ├── package.json                   # Node dependencies
│   ├── vite.config.js                 # Vite configuration
│   └── .env                           # Environment variables
│
├── run-backend.sh                     # Backend startup script
├── run-frontend.sh                    # Frontend startup script
├── run-all.sh                         # Start all services
└── PORT_CONFIG.md                     # Port configuration reference
```

## Service Ports

| Service | Port | URL |
|---------|------|-----|
| Frontend (React) | **5175** | http://localhost:5175 |
| Backend API | **8003** | http://localhost:8003 |
| Swagger UI | **8003** | http://localhost:8003/docs |
| ReDoc | **8003** | http://localhost:8003/redoc |

## Quick Start

### Option 1: Run Everything (Recommended)

```bash
cd intelligent_placement_prep_analyser
bash run-all.sh
```

This will:
- Start backend on port 8003
- Start frontend on port 5175
- Both will automatically open in your browser

### Option 2: Run Services Separately

**Terminal 1 - Backend:**
```bash
cd intelligent_placement_prep_analyser/backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload
```

**Terminal 2 - Frontend:**
```bash
cd intelligent_placement_prep_analyser/frontend/primereact-app
npm install  # First time only
npm run dev
```

### Option 3: Manual Commands

**Backend:**
```bash
cd intelligent_placement_prep_analyser/backend
source venv/bin/activate
pip install -r requirements.txt
python app/database/migrate.py  # Create database tables
uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload
```

**Frontend:**
```bash
cd intelligent_placement_prep_analyser/frontend/primereact-app
npm install
npm run dev  # Runs on port 5175
```

## Database Setup

### Initial Database Setup

```bash
cd intelligent_placement_prep_analyser/backend
source venv/bin/activate
python app/database/migrate.py
```

### Database Connection

- **Type**: PostgreSQL
- **URL**: postgresql://postgres:***@metro.proxy.rlwy.net:32171/railway
- **Tables**: users, resumes, reports

## API Endpoints

### Student Routes
- `GET /student/dashboard` - Get student dashboard data

### Staff Routes
- `GET /staff/students-progress` - Get all students' progress

### Resume Routes
- `POST /resume/upload` - Upload resume

### Interview Routes
- `GET /interview/question` - Generate interview question
- `POST /interview/evaluate` - Evaluate interview answer

## Frontend Configuration

The frontend communicates with the backend using:
- **API Domain**: `http://localhost:8003`
- **Configuration File**: `frontend/primereact-app/src/config/api.js`

All API requests are made using axios with the base URL from the configuration.

## Accessing the Application

### After Starting Services:

1. **Frontend**: Open http://localhost:5175 in your browser
2. **API Docs**: Open http://localhost:8003/docs for Swagger UI
3. **Student Dashboard**: http://localhost:5175 (default route)
4. **Staff Dashboard**: http://localhost:5175/staff

## Environment Variables

### Backend (.env)
```
DATABASE_URL=postgresql://postgres:JwrQyDKXOIZhvjWbcwtxMFdKQHaOTHgb@metro.proxy.rlwy.net:32171/railway
SQLALCHEMY_ECHO=False
SQLALCHEMY_POOL_SIZE=5
SQLALCHEMY_MAX_OVERFLOW=10
GOOGLE_API_KEY=your-google-api-key
```

### Frontend (.env)
```
VITE_API_URL=http://localhost:8003
VITE_APP_TITLE=Placement Prep Analyser
```

## Dependencies

### Backend Python Packages
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `sqlalchemy` - ORM
- `psycopg2-binary` - PostgreSQL driver
- `langchain` - LLM framework
- `langchain-google-genai` - Google Generative AI
- `langchain-text-splitters` - Text processing
- `langchain-community` - Community integrations
- `chromadb` - Vector database
- `pdfplumber` - PDF processing

### Frontend Node Packages
- `react` - UI library
- `react-router-dom` - Routing
- `axios` - HTTP client
- `primereact` - UI components
- `vite` - Build tool

## Troubleshooting

### Backend Won't Start
```bash
# Check if port 8003 is in use
lsof -i :8003

# Kill process on port 8003
pkill -f "uvicorn app.main"

# Restart backend
cd intelligent_placement_prep_analyser/backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8003
```

### Frontend Won't Start
```bash
# Clear node_modules and reinstall
cd frontend/primereact-app
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Database Connection Issues
```bash
# Test database connection
cd backend
source venv/bin/activate
python -c "from app.database.db import engine; print(engine.url)"

# Recreate tables if needed
python app/database/migrate.py
```

### CORS Issues
If frontend can't reach backend, check:
1. Backend is running on port 8003
2. CORS is configured for port 5175 in [backend/app/main.py](backend/app/main.py)
3. Frontend is using correct API URL in [frontend/primereact-app/src/config/api.js](frontend/primereact-app/src/config/api.js)

## Development Notes

- **Hot Reload Enabled**: Both frontend and backend support hot reload during development
- **CORS Configured**: Backend accepts requests from frontend on port 5175
- **Swagger Integration**: API documentation available at http://localhost:8003/docs
- **Environment Variables**: Both services read from `.env` files

## Production Deployment

For production deployment:
1. Build frontend: `npm run build` (generates dist folder)
2. Set environment variables appropriately
3. Use a reverse proxy (nginx) to serve both frontend and backend
4. Update CORS origins to production URLs
5. Use environment-specific configuration files
