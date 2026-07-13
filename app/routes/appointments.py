from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import schemas
from ..database import get_db
from ..services import booking

router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.post("", response_model=schemas.AppointmentOut, status_code=201)
def create_appointment(payload: schemas.AppointmentCreate, db: Session = Depends(get_db)):
    try:
        appointment = booking.book_appointment(
            db=db,
            doctor_id=payload.doctor_id,
            patient_id=payload.patient_id,
            slot_time=payload.slot_time,
        )
    except booking.BookingError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

    return appointment