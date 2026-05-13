from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from pydantic import BaseModel
from typing import List, Dict, Optional
from app.services.Ai_service import get_business_insights, process_chat_message
from app.services.chatbot_service import process_gemini_chat

router = APIRouter()


@router.get("/insights/{file_id}")
async def business_insights(
    file_id: str, 
    lang: str = "en",
    db: Session = Depends(get_db)
):
    try:
        return await get_business_insights(file_id, db, lang=lang)
    except Exception as e:
        print(f"detailed error:{str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ─── Legacy chat endpoint (Kept for backward compatibility) ───
class ChatRequest(BaseModel):
    message: str

@router.post("/chat/{file_id}")
async def chat_with_data_endpoint(
    file_id: str,
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    try:
        return await process_chat_message(file_id, request.message, db)
    except Exception as e:
        print(f"Chat endpoint error:{str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ─── NEW: Gemini-Powered Advanced Chat ───
class GeminiChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[Dict[str, str]]] = []

@router.post("/gemini-chat/{file_id}")
async def gemini_chat_endpoint(
    file_id: str,
    request: GeminiChatRequest,
    db: Session = Depends(get_db)
):
    """Advanced AI chat powered by Google Gemini — supports predictions, 
    deep analysis, conversation memory, and follow-up suggestions."""
    try:
        result = await process_gemini_chat(
            file_id=file_id,
            message=request.message,
            conversation_history=request.conversation_history or [],
            db=db
        )
        return result
    except Exception as e:
        print(f"Gemini chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))