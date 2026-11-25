
from contextvars import ContextVar
from app.database import SessionLocal
from app.models import Doctor, DoctorSlot, Appointment
from app.services.booking_service import book_appointment, cancel_appointment


# Current conversation session
CURRENT_SESSION = ContextVar("current_session", default=None)

# Pending actions for each session
PENDING_ACTIONS = {}


def set_current_session(session_id):
    return CURRENT_SESSION.set(session_id)


def reset_current_session(token):
    CURRENT_SESSION.reset(token)


def get_session_id():
    return CURRENT_SESSION.get()


def prepare_booking(
    patient_name: str,
    phone_number: str,
    doctor_id: int,
    slot_id: int
):
    session_id = get_session_id()

    if not session_id:
        return {"success": False, "message": "Session not found."}

    db = SessionLocal()

    try:
        doctor = db.query(Doctor).filter(
            Doctor.id == doctor_id
        ).first()

        slot = db.query(DoctorSlot).filter(
            DoctorSlot.id == slot_id,
            DoctorSlot.doctor_id == doctor_id
        ).first()

        if not doctor:
            return {"success": False, "message": "Doctor not found."}

        if not slot or slot.status != "available":
            return {"success": False, "message": "Slot unavailable."}

        PENDING_ACTIONS[session_id] = {
            "action": "booking",
            "patient_name": patient_name,
            "phone_number": phone_number,
            "doctor_id": doctor_id,
            "slot_id": slot_id
        }

        return {
            "success": True,
            "confirmation_required": True,
            "message": (
                f"Please confirm booking with {doctor.name} "
                f"on {slot.date} at {slot.time} "
                f"for {patient_name}, phone {phone_number}."
            )
        }

    finally:
        db.close()


def prepare_cancellation(phone_number: str, appointment_id: int):
    session_id = get_session_id()

    if not session_id:
        return {"success": False, "message": "Session not found."}

    db = SessionLocal()

    try:
        appointment = db.query(Appointment).filter(
            Appointment.id == appointment_id,
            Appointment.phone_number == phone_number,
            Appointment.status == "booked"
        ).first()

        if not appointment:
            return {
                "success": False,
                "message": "Active appointment not found."
            }

        doctor = db.query(Doctor).filter(
            Doctor.id == appointment.doctor_id
        ).first()

        PENDING_ACTIONS[session_id] = {
            "action": "cancellation",
            "phone_number": phone_number,
            "appointment_id": appointment_id
        }

        return {
            "success": True,
            "confirmation_required": True,
            "message": (
                f"Please confirm cancellation of appointment "
                f"{appointment_id} with "
                f"{doctor.name if doctor else 'the doctor'} "
                f"on {appointment.appointment_date} "
                f"at {appointment.appointment_time}."
            )
        }

    finally:
        db.close()
        print("PREPARE CANCELLATION SESSION:", session_id)
        print("PENDING ACTION CREATED:", PENDING_ACTIONS)

def confirm_pending_action(session_id: str):
    pending = PENDING_ACTIONS.get(session_id)
    print("CONFIRM SESSION:", session_id)
    print("PENDING ACTIONS:", PENDING_ACTIONS)
    if not pending:
        return {
            "success": False,
            "message": "No pending action found."
        }

    db = SessionLocal()

    try:
        if pending["action"] == "booking":
            result = book_appointment(
                db=db,
                patient_name=pending["patient_name"],
                phone_number=pending["phone_number"],
                doctor_id=pending["doctor_id"],
                slot_id=pending["slot_id"]
            )

        elif pending["action"] == "cancellation":
            result = cancel_appointment(
                db=db,
                phone_number=pending["phone_number"],
                appointment_id=pending["appointment_id"]
            )

        else:
            return {
                "success": False,
                "message": "Unknown pending action."
            }

        if result.get("success"):
            PENDING_ACTIONS.pop(session_id, None)

        return result

    finally:
        db.close()


def reject_pending_action(session_id: str):
    pending = PENDING_ACTIONS.pop(session_id, None)

    if not pending:
        return {
            "success": False,
            "message": "No pending action found."
        }

    return {
        "success": True,
        "message": "Pending action rejected. No changes were made."
    }
