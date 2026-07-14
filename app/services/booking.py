from datetime import date as date_type, datetime, timedelta, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import models


class BookingError(Exception):
    """Raised for any validation failure during booking/reschedule."""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


SLOT_MINUTES = 30


def _validate_slot(db: Session, doctor: models.Doctor, slot_time: datetime) -> None:
    if slot_time.tzinfo is None:
        slot_time = slot_time.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)

    if slot_time <= now:
        raise BookingError("Cannot book a slot in the past.", 400)

    slot_local_time = slot_time.time()
    if not (doctor.work_start <= slot_local_time < doctor.work_end):
        raise BookingError("Slot is outside the doctor's working hours.", 400)

    minutes_since_midnight = slot_time.hour * 60 + slot_time.minute
    if minutes_since_midnight % SLOT_MINUTES != 0:
        raise BookingError("Slot must align to a 30-minute boundary.", 400)


def book_appointment(
    db: Session, doctor_id: int, patient_id: int, slot_time: datetime
) -> models.Appointment:
    doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if doctor is None:
        raise BookingError("Doctor not found.", 404)

    _validate_slot(db, doctor, slot_time)

    appointment = models.Appointment(
        doctor_id=doctor_id,
        patient_id=patient_id,
        slot_time=slot_time,
        cancelled=False,
    )
    db.add(appointment)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise BookingError("This slot is already booked.", 409)

    db.refresh(appointment)
    return appointment


def get_available_slots(
    db: Session, doctor: models.Doctor, target_date: date_type
) -> list[datetime]:
    day_start = datetime.combine(target_date, doctor.work_start, tzinfo=timezone.utc)
    day_end = datetime.combine(target_date, doctor.work_end, tzinfo=timezone.utc)

    booked = db.query(models.Appointment.slot_time).filter(
        models.Appointment.doctor_id == doctor.id,
        models.Appointment.cancelled == False,
        models.Appointment.slot_time >= day_start,
        models.Appointment.slot_time < day_end,
    ).all()
    booked_times = {
        row[0].replace(tzinfo=timezone.utc) if row[0].tzinfo is None else row[0]
        for row in booked
    }

    slots = []
    current = day_start
    while current < day_end:
        if current not in booked_times:
            slots.append(current)
        current += timedelta(minutes=SLOT_MINUTES)

    return slots
def cancel_appointment(
    db: Session, appointment_id: int, reason: str
) -> models.Appointment:
    appointment = (
        db.query(models.Appointment)
        .filter(models.Appointment.id == appointment_id)
        .first()
    )

    if appointment is None:
        raise BookingError("Appointment not found.", 404)

    if appointment.cancelled:
        raise BookingError("Appointment is already cancelled.", 409)

    appointment.cancelled = True
    appointment.cancellation_reason = reason
    db.commit()
    db.refresh(appointment)
    return appointment