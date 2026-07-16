from datetime import time

from fastapi import FastAPI
from .database import Base, engine, SessionLocal
from . import models
from .routes.appointments import router as appointments_router
from .routes.doctors import router as doctors_router
from .routes.patients import router as patients_router

Base.metadata.create_all(bind=engine)

# Seed a default doctor for demo purposes, if none exists
db = SessionLocal()
if db.query(models.Doctor).count() == 0:
    demo_doctor = models.Doctor(
        name="Dr. Jane Otieno",
        email="jane.otieno@example.com",
        work_start=time(9, 0),
        work_end=time(17, 0),
    )
    db.add(demo_doctor)
    db.commit()
db.close()

app = FastAPI(
    title="Clinic Booking API",
    description="Backend API for managing clinic appointments.",
    version="1.0.0",
)

app.include_router(appointments_router)
app.include_router(doctors_router)
app.include_router(patients_router)

@app.get("/")
def root():
    return {"message": "Welcome to the Clinic Booking API"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}