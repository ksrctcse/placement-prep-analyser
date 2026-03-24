
from fastapi import APIRouter

router=APIRouter(prefix="/staff")

@router.get("/students-progress")
def students_progress():
    return {
        "students":[
            {"name":"John","department":"CSE","score":7}
        ]
    }
