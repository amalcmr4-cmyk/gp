from fastapi import HTTPException
from app.database import add_uploaded_file
import os
import uuid

UPLOAD_FOLDER = "uploaded_files"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

async def upload_file_service(file,db):
    
    #file type
    allowed_types = ['.csv', '.xlsx', '.xls']
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_types:
        raise HTTPException(status_code=400, 
                          detail="Extension not allowed!")
    
    file_id=uuid.uuid4().hex[:8]
    unique_name = f"{file_id}_{file.filename}"
    file_location = os.path.join(UPLOAD_FOLDER, unique_name)
    
   #file store 
    try:
        contents = await file.read()
        with open(file_location, "wb") as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(500,"error saving")
    
    file_size=os.path.getsize(file_location)
    
    #save in database
    add_uploaded_file(db=db,file_id=file_id,filename=unique_name,original_name=file.filename,file_size=file_size,
                      file_type=file_ext[1:], file_path=file_location)
    
    return {
        "status":"success",
        "id": file_id,
        "filename": unique_name,
        "size_bytes":file_size,
        "size_mb":round(file_size/(1024*1024),2)   }