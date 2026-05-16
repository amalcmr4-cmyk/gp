from fastapi import HTTPException
import os
import pandas as pd
import numpy as np
import json
import time 
from app.database import get_file, add_analysis_result, AnalyzeStatus

UPLOAD_FOLDER = "uploaded_files"

async def analyze_file_service(file_id: str, db):
    db_file=get_file(db,file_id)
    if not db_file:
        raise HTTPException(404,"file not found in database")
    
    
    #in folder search for the file 
    file_found = None
    for filename in os.listdir(UPLOAD_FOLDER):
        if filename.startswith(file_id + "_"):
            file_found = filename
            break
    
    if not file_found:
        raise HTTPException(404, "File not found")
    
    file_path = os.path.join(UPLOAD_FOLDER, file_found)
    
    #read data in file
    try:
        if file_found.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_found.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path)
        else:
            raise HTTPException(400, "File type not supported")
    except Exception as e:
        raise HTTPException(500, f"Error reading file: {str(e)}")
  
    df= df.fillna("") 
 
   #prepare the response data
   #number of row and columns
    result = {
        "file_name": file_found,
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": list(df.columns),
        "first_rows": df.head(100).to_dict(orient="records") 
    }
    
    add_analysis_result(db=db,file_id=file_id,analyze_type="basic",result=result,
                     status=AnalyzeStatus.completed) 
    
    return result

async def advanced_analysis_service(file_id: str, db):
    db_file = get_file(db, file_id)
    start_time = time.time()
    
    if not db_file:
        raise HTTPException(404, "file not found in database")
    
    #search for file
    file_found = None
    for filename in os.listdir(UPLOAD_FOLDER):
        if filename.startswith(file_id + "_"):
            file_found = filename
            break
    
    if not file_found:
        raise HTTPException(404, "File not found on disk")
    
    file_path = os.path.join(UPLOAD_FOLDER, file_found)
    
    #read file
    try:
        if file_found.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_found.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path)
    except Exception as e:
        raise HTTPException(500, f"Error reading file: {str(e)}")

    
    df.dropna(how='all', inplace=True) 
    df.dropna(axis=1, how='all', inplace=True) 

    if df.empty:
        raise HTTPException(400, "File is empty after removing empty rows/columns")

    #advanced analysis
    analysis = {
        "basic_info": {
            "file_name": file_found,
            "total_rows": len(df),
            "total_columns": len(df.columns)
        },
        "column_analysis": {},
        "numeric_statistics": {},
        "correlation": {},
        "data_quality": {},
        "chart_suggestion": []
    }
    
    #col type
    DATE_KEYWORDS = ['date', 'time', 'year', 'month', 'day', 'timestamp']
    MONEY_KEYWORDS = ['price', 'cost', 'amount', 'salary']
    CATEGORY_KEYWORDS = ['type', 'category', 'region', 'city']
    
    for column in df.columns:
        col_data = df[column]
        numeric_col = pd.to_numeric(col_data, errors='coerce')
        is_actually_numeric = not numeric_col.isna().all()

        is_date_column = any(keyword in str(column).lower() for keyword in DATE_KEYWORDS)
        is_money_column = any(keyword in str(column).lower() for keyword in MONEY_KEYWORDS)
        is_category_column = any(keyword in str(column).lower() for keyword in CATEGORY_KEYWORDS)
        
        col_lower = str(column).lower()
        is_id_column = (
            col_lower in ['id', 'index', 'idx', 'uuid'] or 
            'unnamed' in col_lower or 
            'row_id' in col_lower or 
            'row id' in col_lower or 
            col_lower.endswith('_id') or 
            col_lower.endswith('id')
        )

        
        #col analysis
        analysis["column_analysis"][column] = {
            "data_type": str(col_data.dtype),
            "unique_values": int(col_data.nunique()),
            "missing_values": int(col_data.isna().sum()),
            "is_date_column": is_date_column,
            "is_money_column": is_money_column,
            "is_category_column": is_category_column
        }
        
        chart_suggestions = []
        unique_count = col_data.nunique()

        if not is_actually_numeric and 1 < unique_count <= 15:
            chart_suggestions.append({
                "chart_type": "bar",
                "column": column,
                "reason": f"Categorical data with {unique_count} unique values"
            })
        
        if is_actually_numeric and not is_id_column:
            if unique_count <= 10:
                chart_suggestions.append({"chart_type": "pie", "column": column, "reason": "Low cardinality numeric data"})
            else:
                chart_suggestions.append({"chart_type": "histogram", "column": column, "reason": "Continuous numeric distribution"})

            
           
            valid_nums = numeric_col.dropna()
            if not valid_nums.empty:
                analysis["numeric_statistics"][column] = {
                    "mean": float(valid_nums.mean()),
                    "median": float(valid_nums.median()),
                    "min": float(valid_nums.min()),
                    "max": float(valid_nums.max()),
                    "std": float(valid_nums.std()) if len(valid_nums) > 1 else 0,
                    "count": int(len(valid_nums))
                }

        if is_date_column:
            chart_suggestions.append({"chart_type": "line", "column": column, "reason": "Time-series data detected"})
        
        if chart_suggestions:
            analysis["chart_suggestion"].extend(chart_suggestions)

    #correlation analysis
    meaningful_cols = [c for c in df.columns if not (
        str(c).lower() in ['id', 'index', 'idx', 'uuid'] or 
        'unnamed' in str(c).lower() or 
        'row_id' in str(c).lower() or 
        'row id' in str(c).lower() or 
        str(c).lower().endswith('_id') or 
        str(c).lower().endswith('id')
    )]
    numeric_df = df[meaningful_cols].select_dtypes(include=[np.number]).dropna(axis=1, how='all')
    if len(numeric_df.columns) > 1:
        try:
            corr_matrix = numeric_df.corr().fillna(0)
            for col in corr_matrix.columns:
                analysis["correlation"][col] = {}
                for other_col in corr_matrix.columns:
                    corr_value = corr_matrix.loc[col, other_col]
                    analysis["correlation"][col][other_col] = round(float(corr_value), 3)
        except Exception as e:
            analysis["correlation"] = {"message": f"Could not calculate correlation: {str(e)}"}
    else:
        analysis["correlation"] = {"message": "Need at least 2 numeric columns for correlation"}

    #data quality
    total_cells = int(df.size)
    empty_cells = int(df.isna().sum().sum())
    analysis["data_quality"] = {
        "total_cells": total_cells,
        "empty_cells": empty_cells,
        "completeness_percentage": round((1 - empty_cells/total_cells) * 100, 2) if total_cells > 0 else 0
    }

    #sample data
    analysis["sample_data"] = df.head(5).fillna("(empty)").to_dict(orient="records")

    
    def convert_to_serializable(obj):
        # التعامل مع أنواع أرقام بايثون ونومباي
        if isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            if np.isnan(obj) or np.isinf(obj):
                return None
            return float(obj)
        elif isinstance(obj, (np.ndarray, pd.Series)):
            return obj.tolist()
        # التعامل مع التواريخ (مهم جداً للملفات التي تحتوي على وقت أو تاريخ)
        elif hasattr(obj, 'isoformat'): 
            return obj.isoformat()
        # التعامل مع أي قيمة فارغة تابعة لـ Pandas أو Numpy
        elif pd.isna(obj):
            return None
        return obj

    # قبل تحويل الـ sample_data إلى dict، نضمن استبدال القيم غير المتوافقة مع JSON
    # استبدال الخلايا الفارغة بـ None (والتي تتحول في JSON إلى null)
    df_filled = df.astype(object).where(pd.notna(df), None)
    analysis["sample_data"] = df_filled.head(5).to_dict(orient="records")

    # تحويل القاموس بالكامل إلى نص JSON معالَج بأمان
    try:
        json_str = json.dumps(analysis, default=convert_to_serializable, ensure_ascii=False)
        final_analysis = json.loads(json_str)
    except Exception as json_err:
        import traceback
        print("====== خطأ أثناء تحويل البيانات إلى JSON ======")
        traceback.print_exc()
        raise HTTPException(500, f"JSON serialization failed: {str(json_err)}")

    execution_time = round(time.time() - start_time, 4)
    
    # حفظ النتيجة في قاعدة البيانات
    add_analysis_result(db=db, file_id=file_id, analyze_type="advanced_analysis",
                        result=final_analysis, status=AnalyzeStatus.completed, execution_time=execution_time)
    
    return final_analysis