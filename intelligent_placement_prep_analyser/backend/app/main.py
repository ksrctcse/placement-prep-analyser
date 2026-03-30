
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import staff_routes, resume_routes, interview_routes, auth_routes
from app.routes import student_dashboard, staff_dashboard, test_builder, student_performance

app = FastAPI(
    title="Placement AI Agent",
    description="AI-powered placement preparation analyzer",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Enable CORS for frontend (supports multiple ports)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5175",
        "http://localhost:5176",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:5176",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(staff_routes.router)
app.include_router(student_dashboard.router)
app.include_router(staff_dashboard.router)
app.include_router(test_builder.router)
app.include_router(student_performance.router)
app.include_router(resume_routes.router)
app.include_router(interview_routes.router)

@app.get("/")
def root():
    return {
        "message": "Placement AI Agent Running",
        "docs": "http://localhost:8003/docs",
        "redoc": "http://localhost:8003/redoc"
    }
