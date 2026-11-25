from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.ai_service import generate_response

router = APIRouter(
    prefix="/api/ai",
    tags=["AI Assistant"]
)


class ChatRequest(BaseModel):

    message: str

    session_id: Optional[str] = None


@router.post("/chat")
def chat_with_ai(request: ChatRequest):

    try:
        result = generate_response(
            user_message=request.message,
            session_id=request.session_id
        )

        return {
            "success": True,
            "session_id": result["session_id"],
            "user_message": request.message,
            "ai_response": result["response"]
        }

    except Exception as error:
        print("AI API error:", repr(error))

        raise HTTPException(
            status_code=503,
            detail="AI service temporarily unavailable."
        )