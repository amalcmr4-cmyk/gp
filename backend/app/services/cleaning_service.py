import pandas as pd
import numpy as np
import os
import uuid
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.database import get_file, add_uploaded_file

UPLOAD_FOLDER = "uploaded_files"

def clean_data_service(file_id: str, action: str, db: Session):
    db_file = get_file(db, file_id)
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")

    file_path = db_file.file_path
    
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith('.xlsx') or file_path.endswith('.xls'):
            df = pd.read_excel(file_path)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")
            
        initial_rows = len(df)
            
        if action == "drop_missing":
            df = df.dropna()
        elif action == "fill_mean":
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())
            # For non-numeric, maybe fill with mode or 'Unknown'
            categorical_cols = df.select_dtypes(exclude=[np.number]).columns
            for col in categorical_cols:
                if not df[col].mode().empty:
                    df[col] = df[col].fillna(df[col].mode()[0])
        elif action == "drop_outliers":
            # Simple IQR method for outliers on numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                df = df[(df[col] >= lower_bound) & (df[col] <= upper_bound) | (df[col].isna())]
        else:
            raise HTTPException(status_code=400, detail="Invalid cleaning action")

        final_rows = len(df)

        # Save cleaned file
        new_file_id = uuid.uuid4().hex[:8]
        new_filename = f"{new_file_id}_cleaned_{db_file.original_name}"
        if not new_filename.endswith('.csv'):
            new_filename = new_filename.rsplit('.', 1)[0] + '.csv'
            
        new_file_location = os.path.join(UPLOAD_FOLDER, new_filename)
        
        df.to_csv(new_file_location, index=False)
        file_size = os.path.getsize(new_file_location)
        
        # Add to database
        add_uploaded_file(
            db=db,
            file_id=new_file_id,
            filename=new_filename,
            original_name=f"Cleaned_{db_file.original_name}",
            file_size=file_size,
            file_type="csv",
            file_path=new_file_location
        )

        return {
            "status": "success",
            "message": f"Data cleaned successfully. Rows before: {initial_rows}, Rows after: {final_rows}",
            "new_file_id": new_file_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cleaning data: {str(e)}")
