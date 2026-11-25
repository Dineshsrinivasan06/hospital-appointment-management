
from datetime import date

from app.database import SessionLocal
from app.models import Doctor, DoctorSlot



def check_doctor_availability(search_term: str) -> dict:
    """
    Search doctors by doctor name or medical speciality.
    Return matching doctors and their available appointment slots.

    Args:
        search_term: Doctor name or speciality, for example Arun,
                     Dr. Arun, Cardiology or Dermatology.
    """

    db = SessionLocal()

    try:
        search_term = search_term.strip()

        doctors = db.query(Doctor).filter(
            (Doctor.name.ilike(f"%{search_term}%")) |
            (Doctor.speciality.ilike(f"%{search_term}%"))
        ).all()

        if not doctors:
            return {
                "success": False,
                "message": f"No doctors found for {search_term}"
            }

        results = []

        for doctor in doctors:

            slots = db.query(DoctorSlot).filter(
                DoctorSlot.doctor_id == doctor.id,
                DoctorSlot.status == "available"
            ).all()

            results.append({
                "doctor_id": doctor.id,
                "doctor_name": doctor.name,
                "speciality": doctor.speciality,
                "available_slots": [
                    {
                        "slot_id": slot.id,
                        "date": str(slot.date),
                        "time": slot.time
                    }
                    for slot in slots
                ]
            })

        return {
            "success": True,
            "doctors": results
        }

    finally:
        db.close()
