from datetime import datetime
from pydantic import BaseModel


class AppointmentCreate(BaseModel):
    doctor_id: int
    patient_id: int
    slot_time: datetime


class AppointmentOut(BaseModel):
    id: int
    doctor_id: int
    patient_id: int
    slot_time: datetime
    cancelled: bool
    cancellation_reason: str | None = None

    class Config:
        from_attributes = True


class CancelRequest(BaseModel):
    reason: str


class RescheduleRequest(BaseModel):
    new_slot_time: datetime
    
class AvailableSlot(BaseModel):
    slot_time: datetime