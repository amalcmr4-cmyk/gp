from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.visualization_service import get_visualization_data_service

router = APIRouter(tags=["Visualization"])

@router.get("/{file_id}")
async def get_visualization(
    file_id: str,
    chart_type: str = Query(None, description="chart type (bar, pie, histogram, line, scatter)"),
    column: str = Query(None, description="first column name"),
    column2: str = Query(None, description="second column name(scatter)"),
    db: Session = Depends(get_db)
):

    return await get_visualization_data_service(file_id, chart_type, column, column2, db)