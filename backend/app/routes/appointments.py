
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Literal

from app.database import SessionLocal
from app.models import Appointment, Doctor, DoctorSlot

from app.services.booking_service import (
    book_appointment,
    cancel_appointment
)
from app.routes.admin import get_current_admin


router = APIRouter(
    prefix="/api/appointments",
    tags=["Appointments"]
)


# --------------------------------
# DATABASE CONNECTION
# --------------------------------

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# --------------------------------
# REQUEST SCHEMAS
# --------------------------------

class BookingRequest(BaseModel):
    patient_name: str
    phone_number: str
    doctor_id: int
    slot_id: int


class StatusUpdateRequest(BaseModel):
    status: Literal["booked", "cancelled"]


class EditAppointmentRequest(BaseModel):
    doctor_id: int
    slot_id: int


# --------------------------------
# APPOINTMENT DETAILS
# --------------------------------

def appointment_details(appointment, db):

    doctor = db.query(Doctor).filter(
        Doctor.id == appointment.doctor_id
    ).first()

    return {
        "appointment_id": appointment.id,
        "patient_name": appointment.patient_name,
        "phone_number": appointment.phone_number,
        "doctor_name": doctor.name if doctor else None,
        "doctor_id": appointment.doctor_id,
        "slot_id": appointment.slot_id,
        "date": appointment.appointment_date,
        "time": appointment.appointment_time,
        "status": appointment.status
    }


# --------------------------------
# 1. BOOK APPOINTMENT
# --------------------------------

@router.post("/book")
def create_appointment(
    request: BookingRequest,
    db: Session = Depends(get_db)
):

    return book_appointment(
        db=db,
        patient_name=request.patient_name,
        phone_number=request.phone_number,
        doctor_id=request.doctor_id,
        slot_id=request.slot_id
    )


# --------------------------------
# 2. GET ALL APPOINTMENTS
# --------------------------------

@router.get("/")
def get_appointments(
    db: Session = Depends(get_db)
):

    appointments = db.query(Appointment).all()

    return [
        appointment_details(a, db)
        for a in appointments
    ]


# --------------------------------
# 3. GET APPOINTMENT BY ID
# --------------------------------

@router.get("/{appointment_id}")
def get_appointment(
    appointment_id: int,
    db: Session = Depends(get_db)
):

    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id
    ).first()

    if not appointment:
        raise HTTPException(
            status_code=404,
            detail="Appointment not found"
        )

    return appointment_details(appointment, db)


# --------------------------------
# 4. UPDATE APPOINTMENT STATUS
# --------------------------------

@router.patch("/{appointment_id}/status")
def update_appointment_status(
    appointment_id: int,
    request: StatusUpdateRequest,
    db: Session = Depends(get_db)
):

    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id
    ).first()

    if not appointment:
        raise HTTPException(
            status_code=404,
            detail="Appointment not found"
        )

    slot = db.query(DoctorSlot).filter(
        DoctorSlot.id == appointment.slot_id
    ).first()

    if not slot:
        raise HTTPException(
            status_code=404,
            detail="Associated slot not found"
        )

    new_status = request.status

    if appointment.status == new_status:
        return {
            "success": True,
            "message": "Appointment already has this status",
            "appointment": appointment_details(appointment, db)
        }

    try:

        if new_status == "cancelled":

            if slot.status == "booked":
                slot.status = "available"

            appointment.status = "cancelled"

        elif new_status == "booked":

            if slot.status != "available":
                raise HTTPException(
                    status_code=409,
                    detail="Appointment slot is unavailable"
                )

            slot.status = "booked"
            appointment.status = "booked"

        db.commit()
        db.refresh(appointment)

        return {
            "success": True,
            "message": "Appointment status updated successfully",
            "appointment": appointment_details(appointment, db)
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Unable to update appointment status"
        )


# --------------------------------
# 5. EDIT APPOINTMENT
# CHANGE DOCTOR OR TIME SLOT
# --------------------------------

@router.put("/{appointment_id}/edit")
def edit_appointment(
    appointment_id: int,
    request: EditAppointmentRequest,
    db: Session = Depends(get_db)
):

    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id
    ).first()

    if not appointment:
        raise HTTPException(
            status_code=404,
            detail="Appointment not found"
        )

    if appointment.status != "booked":
        raise HTTPException(
            status_code=400,
            detail="Only booked appointments can be edited"
        )

    new_doctor = db.query(Doctor).filter(
        Doctor.id == request.doctor_id
    ).first()

    if not new_doctor:
        raise HTTPException(
            status_code=404,
            detail="Doctor not found"
        )

    new_slot = db.query(DoctorSlot).filter(
        DoctorSlot.id == request.slot_id,
        DoctorSlot.doctor_id == request.doctor_id
    ).first()

    if not new_slot:
        raise HTTPException(
            status_code=404,
            detail="Selected slot does not belong to this doctor"
        )

    if new_slot.id == appointment.slot_id:

        return {
            "success": True,
            "message": "Existing appointment slot selected",
            "appointment": appointment_details(appointment, db)
        }

    if new_slot.status != "available":
        raise HTTPException(
            status_code=409,
            detail="Selected slot is unavailable"
        )

    old_slot = db.query(DoctorSlot).filter(
        DoctorSlot.id == appointment.slot_id
    ).first()

    if not old_slot:
        raise HTTPException(
            status_code=404,
            detail="Old appointment slot not found"
        )

    try:

        # Release old slot
        old_slot.status = "available"

        # Reserve new slot
        new_slot.status = "booked"

        # Update appointment
        appointment.doctor_id = request.doctor_id
        appointment.slot_id = request.slot_id
        appointment.appointment_date = new_slot.date
        appointment.appointment_time = new_slot.time

        db.commit()
        db.refresh(appointment)

        return {
            "success": True,
            "message": "Appointment updated successfully",
            "appointment": appointment_details(appointment, db)
        }

    except Exception:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Unable to update appointment"
        )


# --------------------------------
# 6. DELETE CANCELLED APPOINTMENT
# --------------------------------

@router.delete("/{appointment_id}")
def delete_appointment(
    appointment_id: int,
    db: Session = Depends(get_db)
):

    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id
    ).first()

    if not appointment:
        raise HTTPException(
            status_code=404,
            detail="Appointment not found"
        )

    if appointment.status != "cancelled":
        raise HTTPException(
            status_code=400,
            detail="Cancel appointment before deleting"
        )

    try:

        db.delete(appointment)
        db.commit()

        return {
            "success": True,
            "message": "Cancelled appointment deleted successfully",
            "appointment_id": appointment_id
        }

    except Exception:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Unable to delete appointment"
        )


# --------------------------------
# 7. CANCEL USING PHONE NUMBER
# --------------------------------

@router.post("/cancel")
def cancel_booking(
    phone_number: str,
    appointment_id: int,
    db: Session = Depends(get_db)
):

    result = cancel_appointment(
        db=db,
        phone_number=phone_number,
        appointment_id=appointment_id
    )

    if not result.get("success"):

        raise HTTPException(
            status_code=404,
            detail=result.get(
                "message",
                "Cancellation failed"
            )
        )

    return result

@router.get("/")
def get_appointments(
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    appointments = db.query(Appointment).all()

    return [
        appointment_details(a, db)
        for a in appointments
    ]