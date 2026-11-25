from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine

from app.models import (
    Doctor,
    DoctorSlot,
    Appointment,
    Admin
)

from app.routes.doctors import router as doctors_router
from app.routes.appointments import router as appointments_router
from app.routes.ai import router as ai_router
from app.routes.voice import router as voice_router
from app.routes.admin import router as admin_router

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Doctor Appointment Assistant",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(doctors_router)
app.include_router(appointments_router)
app.include_router(ai_router)
app.include_router(voice_router)
app.include_router(admin_router)


@app.get("/")
def home():
    return {"message": "API is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}