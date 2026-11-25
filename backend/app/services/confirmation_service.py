
from app.services.secure_confirmation import prepare_booking


def book_appointment_tool(
    patient_name: str,
    phone_number: str,
    doctor_id: int,
    slot_id: int
):
    """
    Prepare an appointment booking.
    Never execute a booking directly.
    Patient confirmation is handled by the backend.
    """

    return prepare_booking(
        patient_name=patient_name,
        phone_number=phone_number,
        doctor_id=doctor_id,
        slot_id=slot_id
    )
