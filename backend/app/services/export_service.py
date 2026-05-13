import os
import uuid
from fastapi import HTTPException
from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.units import inch

from app.database import get_analysis, get_chat_suggestions

REPORT_FOLDER = "exported_reports"
if not os.path.exists(REPORT_FOLDER):
    os.makedirs(REPORT_FOLDER)

def generate_pdf_report_service(file_id: str, db: Session) -> str:
    # Get latest analysis and insights for the file
    analyses = get_analysis(db, file_id)
    if not analyses:
        raise HTTPException(status_code=404, detail="No analysis found for this file.")
    
    analysis = analyses[0] # Get most recent
    suggestions = get_chat_suggestions(db, analysis.id)
    
    report_id = uuid.uuid4().hex[:8]
    pdf_filename = f"Executive_Report_{file_id}_{report_id}.pdf"
    pdf_path = os.path.join(REPORT_FOLDER, pdf_filename)
    
    doc = SimpleDocTemplate(pdf_path, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = styles['Heading1']
    title_style.alignment = 1 # Center
    
    h2_style = styles['Heading2']
    h2_style.textColor = colors.HexColor("#333333")
    
    normal_style = styles['Normal']
    normal_style.fontSize = 11
    normal_style.leading = 14
    
    Story = []
    
    Story.append(Paragraph("DataWizard Executive Audit Report", title_style))
    Story.append(Spacer(1, 0.2 * inch))
    
    # Add Data Quality
    Story.append(Paragraph("Data Quality & Overview", h2_style))
    try:
        basic_info = analysis.result.get('basic_info', {})
        dq = analysis.result.get('data_quality', {})
        Story.append(Paragraph(f"<b>Total Rows:</b> {basic_info.get('total_rows', 'N/A')}", normal_style))
        Story.append(Paragraph(f"<b>Total Columns:</b> {basic_info.get('total_columns', 'N/A')}", normal_style))
        Story.append(Paragraph(f"<b>Completeness:</b> {dq.get('completeness_percentage', 'N/A')}%", normal_style))
    except Exception as e:
        Story.append(Paragraph("Error loading basic info.", normal_style))
    
    Story.append(Spacer(1, 0.2 * inch))
    
    # Add Business Insights if available
    if suggestions:
        import json
        try:
            latest_suggestion = json.loads(suggestions[0].suggestion_text)
            insights = latest_suggestion.get("business_insights", {})
            
            Story.append(Paragraph("AI Business Insights", h2_style))
            
            for key, value in insights.items():
                if key in ["chart_suggestion", "summary"] or not value: continue
                # format title
                title = key.replace("_", " ").title()
                Story.append(Paragraph(f"<b>{title}:</b>", normal_style))
                Story.append(Paragraph(value, normal_style))
                Story.append(Spacer(1, 0.1 * inch))
                
        except Exception as e:
            Story.append(Paragraph("Could not parse AI insights.", normal_style))
            
    doc.build(Story)
    
    return pdf_path
