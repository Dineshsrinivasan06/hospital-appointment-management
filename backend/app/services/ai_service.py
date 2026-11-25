
import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import ServerError

from app.services.doctor_tools import check_doctor_availability
from app.services.confirmation_service import book_appointment_tool
from app.services.cancellation_service import (
    find_patient_appointments,
    cancel_patient_appointment
)
import uuid
from app.services.secure_confirmation import (
    set_current_session,
    reset_current_session,
    confirm_pending_action,
    reject_pending_action,
    PENDING_ACTIONS
)

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY is missing from .env")

client = genai.Client(api_key=API_KEY)

CHAT_SESSIONS = {}

SYSTEM_PROMPT = """
You are a friendly AI Doctor Appointment Assistant.

You can help patients:
1. Find doctors by speciality.
2. Check available appointment slots.
3. Book appointments.
4. Cancel appointments.

DOCTOR SEARCH RULES:

1. Search doctors by name or speciality.
2. If patient says Dr. Arun, search using Arun.
3. Show only doctors returned by the database.
4. Display actual available slots.
5. Never invent doctor details.
6. If no doctor is found, ask the patient
   whether they want to search by speciality.


BOOKING RULES:


1. Ask the patient for their full name.
2. Ask for their registered phone number.
3. Check available doctors and slots.
4. Show actual available dates and times.
5. Ask the patient to select a slot.
6. Use the actual doctor_id and slot_id
   returned by the availability tool.
7. Never invent doctor IDs or slot IDs.
8. Repeat the following details:
   - Patient name
   - Phone number
   - Doctor name
   - Appointment date
   - Appointment time
9. Ask for explicit confirmation.
10. Only after confirmation call
    book_appointment_tool with confirmed=True.
11. Never book without confirmation.
12. Never ask for patient ID unless the
    application actually requires it.

CANCELLATION RULES:
1. Ask for registered phone number.
2. Find active appointments.
3. Show appointment details.
4. Ask which appointment to cancel.
5. Repeat appointment details.
6. Ask explicit confirmation.
7. Cancel only after confirmation.

Never invent appointment details.
Never diagnose medical conditions.
Speak naturally and politely.
SECURE CONFIRMATION RULES:
1. Booking and cancellation tools only prepare pending actions.
2. Never claim an appointment is booked or cancelled
   when the tool only requests confirmation.
3. Show the complete pending action details.
4. Ask the patient for explicit confirmation.
5. Wait for the patient's next message.
6. Never call booking or cancellation tools with confirmed=True.
7. The backend handles final confirmation.
"""


def generate_response(user_message: str, session_id: str = None):

    if not session_id:
        session_id = str(uuid.uuid4())

    try:
        if session_id not in CHAT_SESSIONS:

            CHAT_SESSIONS[session_id] = client.chats.create(
                model="gemini-3.5-flash-lite",
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    tools=[
                        check_doctor_availability,
                        book_appointment_tool,
                        find_patient_appointments,
                        cancel_patient_appointment
                    ]
                )
            )

        chat = CHAT_SESSIONS[session_id]

        # Only explicit standalone confirmation phrases.
        normalized = user_message.strip().lower()

        yes_messages = {
            "yes",
            "yes confirm",
            "yes i confirm",
            "i confirm",
            "confirm",
            "i agree",
            "please proceed",
            "yes please"
        }

        no_messages = {
            "no",
            "no cancel",
            "no don't",
            "do not proceed",
            "i do not confirm",
            "reject"
        }

        pending = PENDING_ACTIONS.get(session_id)

        if pending and normalized in yes_messages:
            result = confirm_pending_action(session_id)

            return {
                "session_id": session_id,
                "response": result
            }

        if pending and normalized in no_messages:
            result = reject_pending_action(session_id)

            return {
                "session_id": session_id,
                "response": result
            }

        # Set current session for backend tools.
        token = set_current_session(session_id)

        try:
            response = chat.send_message(user_message)
        finally:
            reset_current_session(token)

        return {
            "session_id": session_id,
            "response": response.text
        }

    except Exception as error:
        print("Gemini error:", repr(error))
        raise
    print("CURRENT SESSION:", session_id)
    print("PENDING ACTION:", PENDING_ACTIONS.get(session_id))

def test_gemini():

    models = [
        
        "gemini-3.5-flash-lite",
       
    ]

    for model in models:

        try:
            print(f"Testing model: {model}")

            response = client.models.generate_content(
                model=model,
                contents="Say Hello"
            )

            print("SUCCESS:", model)
            print(response.text)

            return model

        except Exception as error:
            print("FAILED:", model, repr(error))

    return "All models failed"


def test_function_calling():

    try:
        chat = client.chats.create(
            model="gemini-3.5-flash-lite",
            config=types.GenerateContentConfig(
                tools=[check_doctor_availability]
            )
        )

        response = chat.send_message(
            "Find available cardiology doctors"
        )

        print("AI RESPONSE:", response.text)

    except Exception as error:
        print("FUNCTION CALL ERROR:", repr(error))