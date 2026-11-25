
from gtts import gTTS
import tempfile
import os


def text_to_speech(text: str, language: str = "en"):

    if not text or not text.strip():
        raise ValueError("Text cannot be empty")

    if len(text) > 3000:
        raise ValueError("Text is too long")

    temp_file = tempfile.NamedTemporaryFile(
        suffix=".mp3",
        delete=False
    )

    file_path = temp_file.name
    temp_file.close()

    try:
        tts = gTTS(
            text=text,
            lang=language,
            slow=False
        )

        tts.save(file_path)

        return file_path

    except Exception:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise
