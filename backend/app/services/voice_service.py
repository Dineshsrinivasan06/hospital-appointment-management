
import speech_recognition as sr


def speech_to_text(audio_file):

    recognizer = sr.Recognizer()

    try:
        with sr.AudioFile(audio_file) as source:

            audio = recognizer.record(source)

        text = recognizer.recognize_google(
            audio,
            language="en-IN"
        )

        return {
            "success": True,
            "text": text
        }

    except sr.UnknownValueError:

        return {
            "success": False,
            "message": "Could not understand audio."
        }

    except sr.RequestError as error:

        return {
            "success": False,
            "message": f"Speech recognition error: {error}"
        }

    except Exception as error:

        return {
            "success": False,
            "message": str(error)
        }
