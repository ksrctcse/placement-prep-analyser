
from fastapi import FastAPI
from app.routes import student_routes, staff_routes, resume_routes, interview_routes

app = FastAPI(title="Placement AI Agent")

app.include_router(student_routes.router)
app.include_router(staff_routes.router)
app.include_router(resume_routes.router)
app.include_router(interview_routes.router)

@app.get("/")
def root():
    return {"message": "Placement AI Agent Running"}
