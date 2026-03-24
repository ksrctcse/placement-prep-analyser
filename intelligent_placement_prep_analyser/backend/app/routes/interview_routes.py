
from fastapi import APIRouter
from app.services.interview_service import generate_question,evaluate_answer

router=APIRouter(prefix="/interview")

@router.get("/question")
def question():
    return {"question":generate_question()}

@router.post("/evaluate")
def evaluate(data:dict):
    feedback=evaluate_answer(data["answer"])
    return {"feedback":feedback}
