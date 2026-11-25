from sqlalchemy.orm import Session

from app.models import Doctor, DoctorSlot, Appointment


def book_appointment(
    db: Session,
    patient_name: str,
    phone_number: str,
    doctor_id: int,
    slot_id: int
):

    # Check doctor exists
    doctor = db.query(Doctor).filter(
        Doctor.id == doctor_id
    ).first()

    if not doctor:
        return {
            "success": False,
            "message": "Doctor not found"
        }

    # Check slot exists
    slot = db.query(DoctorSlot).filter(
        DoctorSlot.id == slot_id,
        DoctorSlot.doctor_id == doctor_id
    ).first()

    if not slot:
        return {
            "success": False,
            "message": "Slot not found"
        }

    # Check slot availability
    if slot.status != "available":
        return {
            "success": False,
            "message": "This slot is already booked"
        }

    # Create appointment
    appointment = Appointment(
        patient_name=patient_name,
        phone_number=phone_number,
        doctor_id=doctor_id,
        slot_id=slot_id,
        appointment_date=slot.date,
        appointment_time=slot.time,
        status="booked"
    )

    # Update slot status
    slot.status = "booked"

    # Save changes
    db.add(appointment)

    db.commit()

    db.refresh(appointment)

    return {
        "success": True,
        "message": "Appointment booked successfully",
        "appointment": {
            "appointment_id": appointment.id,
            "patient_name": appointment.patient_name,
            "phone_number": appointment.phone_number,
            "doctor_name": doctor.name,
            "speciality": doctor.speciality,
            "date": appointment.appointment_date,
            "time": appointment.appointment_time,
            "status": appointment.status
        }
    }
    
def cancel_appointment(
    db,
    phone_number: str,
    appointment_id: int
):

    # Find appointment
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id,
        Appointment.phone_number == phone_number
    ).first()

    # Appointment not found
    if not appointment:
        return {
            "success": False,
            "message": "Appointment not found"
        }

    # Check if already cancelled
    if appointment.status == "cancelled":
        return {
            "success": False,
            "message": "Appointment already cancelled"
        }

    # Find booked slot
    slot = db.query(DoctorSlot).filter(
        DoctorSlot.id == appointment.slot_id
    ).first()

    # Cancel appointment
    appointment.status = "cancelled"

    # Make slot available again
    if slot:
        slot.status = "available"

    # Save changes
    db.commit()

    return {
        "success": True,
        "message": "Appointment cancelled successfully",
        "appointment_id": appointment.id,
        "status": appointment.status
    }