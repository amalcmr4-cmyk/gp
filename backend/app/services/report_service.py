from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.database import get_analysis, get_file
import os
import json
import uuid
import numpy as np
import pandas as pd

REPORTS_FOLDER = "reports"
os.makedirs(REPORTS_FOLDER, exist_ok=True)

class ReportGenerator:
    @staticmethod
    def generate_summary(analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        summary = {
            "total_rows": analysis_result.get("basic_info", {}).get("total_rows", 0),
            "total_columns": analysis_result.get("basic_info", {}).get("total_columns", 0),
            "quality_score": analysis_result.get("data_quality", {}).get("completeness_percentage", 0),
            "warnings": [],
            "insights": []
        }
        
        stats = analysis_result.get("numeric_statistics", {})
        for col, val in stats.items():
            if val.get('std', 0) > val.get('mean', 0):
                summary["warnings"].append(f"High variance detected in '{col}'")
            if val.get('count', 0) > 0 and val.get('min') == val.get('max'):
                summary["warnings"].append(f"Column '{col}' has constant values.")

        score = summary["quality_score"]
        if score < 50: summary["warnings"].append("Low data quality")
        elif score < 80: summary["warnings"].append("Moderate data quality")
        else: summary["insights"].append("Excellent data quality")

        return summary

def convert_to_serializable(obj):
    if isinstance(obj, (np.integer, np.int64, np.int32)): return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        if np.isnan(obj) or np.isinf(obj): return None
        return float(obj)
    elif isinstance(obj, (np.ndarray, pd.Series)): return obj.tolist()
    elif pd.isna(obj): return None
    elif isinstance(obj, datetime): return obj.isoformat()
    return obj

def generate_report(file_id: str, db: Session) -> Dict[str, Any]:
    file_info = get_file(db, file_id)
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found")

    analyses = get_analysis(db, file_id)
    if not analyses:
        raise HTTPException(status_code=404, detail="No analysis found")

    report_id = str(uuid.uuid4())
    report = {
        "report_id": report_id,
        "file_info": {
            "file_id": file_info.id,
            "original_name": file_info.original_name,
            "file_size_mb": round(file_info.file_size / (1024 * 1024), 2),
            "uploaded_at": file_info.upload_time.isoformat()
        },
        "analysis_count": len(analyses),
        "generated_at": datetime.now().isoformat(),
        "analyses": []
    }

    for analysis in analyses:
        analysis_entry = {
            "analysis_id": analysis.id,
            "analysis_type": analysis.analyze_type,
            "status": analysis.status.value if hasattr(analysis.status, 'value') else analysis.status,
            "date_time": getattr(analysis, 'date_time', 
                                 datetime.now()).isoformat() if hasattr(analysis, 'date_time') 
                                 and analysis.date_time else datetime.now().isoformat(),
        }
        if analysis.result:
            safe_result = json.loads(json.dumps(analysis.result, default=convert_to_serializable)) 
            analysis_entry["summary"] = ReportGenerator.generate_summary(safe_result)
        else:
            analysis_entry["summary"] = {"warnings": ["No result data available"], "insights": []}
        report["analyses"].append(analysis_entry)
        
    filename = f"report_{file_id}_{report_id[:8]}.json"
    file_path = os.path.join(REPORTS_FOLDER, filename)

    try:
        safe_report = json.loads(json.dumps(report, default=convert_to_serializable)) 
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(safe_report, f, indent=4, ensure_ascii=False)  
        safe_report["saved_path"] = file_path
        return safe_report
    except Exception as e:
        report["saved_path"] = f"error:{str(e)}" 
        return report

def quick_report(file_id: str, db: Session) -> Dict[str, Any]:
    report = generate_report(file_id, db)
    return {
        "file_name": report["file_info"]["original_name"],
        "total_analyses": report["analysis_count"],
        "latest_analysis": report["analyses"][0] if report["analyses"] else None
    }

def list_reports(file_id: Optional[str] = None) -> List[Dict[str, Any]]:
    if not os.path.exists(REPORTS_FOLDER): return []
    
    reports_list = []
    for filename in os.listdir(REPORTS_FOLDER):
        if not filename.endswith('.json'): continue
        if file_id and f"report_{file_id}" not in filename: continue
        
        filepath = os.path.join(REPORTS_FOLDER, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                reports_list.append({
                    "filename": filename,
                    "report_id": data.get("report_id"),
                    "generated_at": data.get("generated_at"),
                    "original_name": data.get("file_info", {}).get("original_name")
                })
        except: continue
    return reports_list

def get_report_path(file_id: str) -> Optional[str]:
    if not os.path.exists(REPORTS_FOLDER): return None
    for filename in os.listdir(REPORTS_FOLDER):
        if filename.startswith(f"report_{file_id}"):
            return os.path.join(REPORTS_FOLDER, filename)
    return None

def load_report(path: str) -> Dict[str, Any]:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def delete_report(path: str) -> bool:
    try:
        os.remove(path)
        return True
    except: return False