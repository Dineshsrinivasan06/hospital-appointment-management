from datetime import date, timedelta

from app.database import SessionLocal, Base, engine
from app.models import Doctor, DoctorSlot


# Create database tables
Base.metadata.create_all(bind=engine)


def add_sample_data():

    db = SessionLocal()

    try:

        # Prevent duplicate sample data
        if db.query(Doctor).first():
            print("Sample doctors already exist.")
            return

        doctors = [
            Doctor(
                name="Dr. Arun",
                speciality="Cardiology",
                experience=8
            ),

            Doctor(
                name="Dr. Priya",
                speciality="Dermatology",
                experience=5
            ),

            Doctor(
                name="Dr. Kumar",
                speciality="Orthopaedics",
                experience=10
            ),

            Doctor(
                name="Dr. Meena",
                speciality="General Physician",
                experience=6
            )
        ]

        db.add_all(doctors)

        db.commit()

        # Fetch doctors after inserting
        doctors = db.query(Doctor).all()

        # Create slots for the next 7 days
        times = [
            "09:00 AM",
            "10:00 AM",
            "11:00 AM",
            "12:00 PM",
            "02:00 PM",
            "03:00 PM",
            "04:00 PM"
        ]

        for doctor in doctors:

            for day in range(1, 8):

                appointment_date = (
                    date.today() + timedelta(days=day)
                ).isoformat()

                for time in times:

                    slot = DoctorSlot(
                        doctor_id=doctor.id,
                        date=appointment_date,
                        time=time,
                        status="available"
                    )

                    db.add(slot)

        db.commit()

        print("Doctors and slots created successfully!")

    except Exception as error:

        db.rollback()

        print("Error:", error)

    finally:

        db.close()


if __name__ == "__main__":
    add_sample_data()