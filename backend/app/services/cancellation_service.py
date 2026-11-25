
from app.database import SessionLocal
from app.models import Appointment, Doctor
from app.services.secure_confirmation import prepare_cancellation


def find_patient_appointments(phone_number: str):
    """
    Find active appointments using patient's phone number.
    """

    db = SessionLocal()

    try:
        appointments = db.query(Appointment).filter(
            Appointment.phone_number == phone_number,
            Appointment.status == "booked"
        ).all()

        results = []

        for appointment in appointments:
            doctor = db.query(Doctor).filter(
                Doctor.id == appointment.doctor_id
            ).first()

            results.append({
                "appointment_id": appointment.id,
                "doctor": doctor.name if doctor else "Unknown",
                "date": appointment.appointment_date,
                "time": appointment.appointment_time,
                "status": appointment.status
            })

        return {
            "success": True,
            "appointments": results
        }

    finally:
        db.close()


def cancel_patient_appointment(
    phone_number: str,
    appointment_id: int
):
    """
    Prepare cancellation. Do not cancel directly.
    Backend confirmation is required.
    """

    return prepare_cancellation(
        phone_number=phone_number,
        appointment_id=appointment_id
    )
