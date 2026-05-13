from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.analysis_service import analyze_file_service, advanced_analysis_service

router = APIRouter()

@router.get("/analyze/{file_id}")
async def analyze_file(file_id: str, db: Session = Depends(get_db)):
    return await analyze_file_service(file_id, db)

from pydantic import BaseModel

class CleanRequest(BaseModel):
    action: str

@router.get("/advanced/{file_id}")
async def advanced_analysis(file_id: str, db: Session = Depends(get_db)):
    return await advanced_analysis_service(file_id, db)

@router.post("/clean/{file_id}")
async def clean_file(file_id: str, request: CleanRequest, db: Session = Depends(get_db)):
    from app.services.cleaning_service import clean_data_service
    return clean_data_service(file_id, request.action, db)