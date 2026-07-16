from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("/{patient_id}/appointments", response_model=list[schemas.AppointmentOut])
def get_patient_appointments(patient_id: int, db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    appointments = (
        db.query(models.Appointment)
        .filter(
            models.Appointment.patient_id == patient_id,
            models.Appointment.cancelled == False,
            models.Appointment.slot_time >= now,
        )
        .order_by(models.Appointment.slot_time.asc())
        .all()
    )
    return appointments