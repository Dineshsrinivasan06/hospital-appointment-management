from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


# -------------------------
# DOCTOR TABLE
# -------------------------

class Doctor(Base):

    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)

    speciality = Column(String, nullable=False)

    experience = Column(Integer, nullable=False)

    # Doctor has multiple slots
    slots = relationship(
        "DoctorSlot",
        back_populates="doctor"
    )


# -------------------------
# DOCTOR SLOT TABLE
# -------------------------

class DoctorSlot(Base):

    __tablename__ = "doctor_slots"

    id = Column(Integer, primary_key=True, index=True)

    doctor_id = Column(
        Integer,
        ForeignKey("doctors.id"),
        nullable=False
    )

    date = Column(String, nullable=False)

    time = Column(String, nullable=False)

    status = Column(
        String,
        default="available"
    )

    doctor = relationship(
        "Doctor",
        back_populates="slots"
    )


# -------------------------
# APPOINTMENT TABLE
# -------------------------

class Appointment(Base):

    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)

    patient_name = Column(String, nullable=False)

    phone_number = Column(String, nullable=False)

    doctor_id = Column(
        Integer,
        ForeignKey("doctors.id"),
        nullable=False
    )

    slot_id = Column(
        Integer,
        ForeignKey("doctor_slots.id"),
        nullable=False
    )

    appointment_date = Column(String, nullable=False)

    appointment_time = Column(String, nullable=False)

    status = Column(
        String,
        default="booked"
    )
    
    
# -------------------------
# ADMIN TABLE
# -------------------------

class Admin(Base):
    __tablename__ = "admins"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    username = Column(
        String,
        unique=True,
        nullable=False
    )

    email = Column(
        String,
        unique=True,
        nullable=True
    )

    hashed_password = Column(
        String,
        nullable=False
    )