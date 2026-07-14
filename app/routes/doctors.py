from datetime import date as date_type

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..services import booking

router = APIRouter(prefix="/doctors", tags=["doctors"])


@router.get("/{doctor_id}/availability", response_model=list[schemas.AvailableSlot])
def get_availability(doctor_id: int, date: date_type, db: Session = Depends(get_db)):
    doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if doctor is None:
        raise HTTPException(status_code=404, detail="Doctor not found.")

    slots = booking.get_available_slots(db, doctor, date)
    return [schemas.AvailableSlot(slot_time=s) for s in slots]