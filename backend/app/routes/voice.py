
import os
import tempfile

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks

from app.services.voice_service import speech_to_text
from app.services.ai_service import generate_response
from fastapi.responses import FileResponse
# from fastapi.background import BackgroundTasks
from app.services.tts_service import text_to_speech
# from fastapi import BackgroundTasks
router = APIRouter(
    prefix="/api/voice",
    tags=["Voice Assistant"]
)


@router.post("/speech-to-text")
async def convert_speech(
    audio: UploadFile = File(...)
):

    if audio.content_type not in [
        "audio/wav",
        "audio/x-wav"
    ]:
        raise HTTPException(
            status_code=400,
            detail="Please upload a WAV audio file."
        )

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            suffix=".wav",
            delete=False
        ) as temp:

            content = await audio.read()

            if len(content) > 10 * 1024 * 1024:
                raise HTTPException(
                    status_code=413,
                    detail="Audio file is too large."
                )

            temp.write(content)
            temp_path = temp.name

        result = speech_to_text(temp_path)

        return result

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

from typing import Optional
from pydantic import BaseModel


class VoiceChatRequest(BaseModel):
    text: str
    session_id: Optional[str] = None


@router.post("/voice-chat")
async def voice_chat(request: VoiceChatRequest):

    if not request.text.strip():
        raise HTTPException(
            status_code=400,
            detail="Voice text cannot be empty."
        )

    try:
        result = generate_response(
            user_message=request.text,
            session_id=request.session_id
        )

        return {
            "success": True,
            "session_id": result["session_id"],
            "recognized_text": request.text,
            "ai_response": result["response"]
        }

    except Exception as error:
        print("Voice chat error:", repr(error))

        raise HTTPException(
            status_code=503,
            detail="AI service temporarily unavailable."
        )



import os

@router.post("/text-to-speech")
async def convert_text_to_speech(
    text: str,
    background_tasks: BackgroundTasks,
    language: str = "en"
):
    file_path = None

    try:
        if language not in ["en", "ta", "hi"]:
            raise HTTPException(
                status_code=400,
                detail="Supported languages: en, ta, hi"
            )

        file_path = text_to_speech(text, language)

        background_tasks.add_task(os.remove, file_path)

        return FileResponse(
            path=file_path,
            media_type="audio/mpeg",
            filename="ai_response.mp3",
            background=background_tasks
        )

    except HTTPException:
        raise

    except Exception as error:
        print("TTS ERROR:", repr(error))
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

        raise HTTPException(
            status_code=503,
            detail=str(error)
        )
