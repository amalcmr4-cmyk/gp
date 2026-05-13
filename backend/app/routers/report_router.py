from fastapi import APIRouter, Depends, Query,HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.services.report_service import generate_report, quick_report, list_reports
from app.services.report_service import get_report_path, load_report, delete_report

router = APIRouter()

from fastapi.responses import FileResponse

@router.get("/{file_id}")
async def get_full_report(
    file_id: str,
    db: Session = Depends(get_db)
):
    return generate_report(file_id, db)


@router.get("/{file_id}/export/pdf")
async def export_pdf_report(
    file_id: str,
    db: Session = Depends(get_db)
):
    from app.services.export_service import generate_pdf_report_service
    pdf_path = generate_pdf_report_service(file_id, db)
    return FileResponse(path=pdf_path, filename=f"Report_{file_id}.pdf", media_type="application/pdf")


@router.get("/{file_id}/quick")
async def get_quick_report(
    file_id: str,
    db: Session = Depends(get_db)
):
    return quick_report(file_id, db)


@router.get("/{file_id}/list")
async def list_file_reports(
    file_id: str,
    db: Session = Depends(get_db)
):
    reports = list_reports(file_id)
    return {
        "file_id": file_id,
        "total_reports": len(reports),
        "reports": reports
    }


@router.get("/download/{file_id}")
async def download_report(
    file_id: str,
):
    report_path = get_report_path(file_id)
    if not report_path:
        raise HTTPException(status_code=404, detail="Report not found")
    
    report = load_report(report_path)
    return report


@router.delete("/{file_id}")
async def delete_file_report(
    file_id: str
):
    report_path = get_report_path(file_id)
    if not report_path:
        raise HTTPException(status_code=404, detail="Report not found")
    
    deleted = delete_report(report_path)
    if deleted:
        return {"message": f"Report for file {file_id} deleted successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete report")