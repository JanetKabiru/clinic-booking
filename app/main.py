from fastapi import FastAPI
from .database import Base, engine
from . import models
from .routes.appointments import router as appointments_router
from .routes.doctors import router as doctors_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Clinic Booking API",
    description="Backend API for managing clinic appointments.",
    version="1.0.0",
)

app.include_router(appointments_router)
app.include_router(doctors_router)


@app.get("/")
def root():
    return {"message": "Welcome to the Clinic Booking API"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}