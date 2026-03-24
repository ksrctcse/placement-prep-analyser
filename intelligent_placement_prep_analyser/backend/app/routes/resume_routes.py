
from fastapi import APIRouter,UploadFile
from app.services.resume_service import process_resume

router=APIRouter(prefix="/resume")

@router.post("/upload")
async def upload_resume(file:UploadFile):
    result=await process_resume(file)
    return {"message":result}
