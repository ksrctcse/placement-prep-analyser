# Port Configuration for Placement Prep Analyser

## Services and Ports

| Service | Port | URL |
|---------|------|-----|
| Frontend (React/Vite) | 5175 | http://localhost:5175 |
| Backend API (FastAPI) | 8003 | http://localhost:8003 |
| Swagger UI (API Docs) | 8003 | http://localhost:8003/docs |
| ReDoc (API Docs)      | 8003 | http://localhost:8003/redoc |

## Running the Services

### Option 1: Run All Services Together
```bash
bash run-all.sh
```

### Option 2: Run Services Separately

**Backend (Port 8003):**
```bash
bash run-backend.sh
```

**Frontend (Port 5175):**
```bash
bash run-frontend.sh
```

### Option 3: Manual Start

**Backend:**
```bash
cd intelligent_placement_prep_analyser/backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload
```

**Frontend:**
```bash
cd intelligent_placement_prep_analyser/frontend/primereact-app
npm install  # First time only
npm run dev  # Runs on port 5175
```

## API Integration

The frontend is configured to communicate with the backend at `http://localhost:8003`.

API endpoints referenced in frontend:
- `http://localhost:8003/student/dashboard`
- `http://localhost:8003/staff/students-progress`

## Notes

- **Note about Swagger on Port 8002:** FastAPI serves Swagger UI on the same port as the API (8003). If you need Swagger on a separate port (8002), you would need to set up a reverse proxy or run a separate Swagger UI instance. For standard FastAPI applications, Swagger is served at `/docs` on the same server.

- The frontend uses Vite as the build tool, which provides hot module replacement during development.

- CORS is enabled on the backend to allow requests from the frontend on port 5175.

- Both the frontend and backend use environment variables for configuration (`.env` files).
