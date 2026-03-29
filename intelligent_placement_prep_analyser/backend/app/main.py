
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import student_routes, staff_routes, resume_routes, interview_routes, auth_routes
from app.config.settings import settings
from app.database.db import engine, Base

# Create database tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Backend API for Placement Prep Analyser with AI assistance"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_routes.router)
app.include_router(student_routes.router)
app.include_router(staff_routes.router)
app.include_router(resume_routes.router)
app.include_router(interview_routes.router)

@app.get("/")
def root():
    return {
        "message": "Placement Prep Analyser API Running",
        "version": "1.0.0",
        "docs": "/docs"
    }
