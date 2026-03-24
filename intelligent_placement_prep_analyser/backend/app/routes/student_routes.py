
from fastapi import APIRouter

router=APIRouter(prefix="/student")

@router.get("/dashboard")
def dashboard():
    return {
        "progress":"Good",
        "recommendation":"Practice system design"
    }
