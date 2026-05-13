from fastapi import APIRouter,File,UploadFile,Depends,HTTPException
from sqlalchemy.orm import Session
from app.services.file_service import upload_file_service
import os
from app.database import UploadedFile,get_file,get_db

router= APIRouter()

@router.post("/uploadfile/")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    result = await upload_file_service(file, db)
    return result

@router.delete("/delete-file/{file_id}")
async def delete_file(file_id: str, db: Session = Depends(get_db)):
    db_file = get_file(db, file_id)
    if not db_file:
        raise HTTPException(404, "File not found")
    
    #delete file from folder
    file_deleted=False
    if os.path.exists(db_file.file_path):
        os.remove(db_file.file_path)
        file_deleted=True

    db_file.is_deleted = True
    db.commit()

    return {"status": "success",
            "message": "File and related analysis deleted successfully",
            "file_deleted_from_disk":file_deleted}

@router.get("/files")
async def get_all_files(db: Session = Depends(get_db)):
    files = db.query(UploadedFile).filter(UploadedFile.is_deleted==False).all()

    result = []
    for f in files:
        result.append({
            "id":f.id,

            "filename":f.unique_name, 
            "name":f.original_name,   
            "filesize":f.file_size,  
            "filetype":f.file_type,  
            "upload_time":f.upload_time
        })
    return result