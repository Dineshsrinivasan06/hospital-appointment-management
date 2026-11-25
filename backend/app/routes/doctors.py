from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Doctor, DoctorSlot


router = APIRouter(
    prefix="/api/doctors",
    tags=["Doctors"]
)


# Database connection dependency
def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# Get all doctors
@router.get("/")
def get_doctors(db: Session = Depends(get_db)):

    doctors = db.query(Doctor).all()

    return doctors


# Get doctor by ID
@router.get("/{doctor_id}")
def get_doctor(
    doctor_id: int,
    db: Session = Depends(get_db)
):

    doctor = db.query(Doctor).filter(
        Doctor.id == doctor_id
    ).first()

    if not doctor:
        return {
            "error": "Doctor not found"
        }

    return doctor


# Get available slots for a doctor
@router.get("/{doctor_id}/slots")
def get_doctor_slots(
    doctor_id: int,
    db: Session = Depends(get_db)
):

    slots = db.query(DoctorSlot).filter(
        DoctorSlot.doctor_id == doctor_id,
        DoctorSlot.status == "available"
    ).all()

    return slots