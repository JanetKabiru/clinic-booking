from sqlalchemy import Column, Integer, String, Time, DateTime, Boolean, ForeignKey, Index, text
from .database import Base


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    work_start = Column(Time, nullable=False)
    work_end = Column(Time, nullable=False)


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False)
    patient_id = Column(Integer, nullable=False, index=True)
    slot_time = Column(DateTime, nullable=False)
    cancelled = Column(Boolean, default=False, nullable=False)
    cancellation_reason = Column(String, nullable=True)

    __table_args__ = (
        Index(
            "idx_unique_active_appointment",
            "doctor_id",
            "slot_time",
            unique=True,
            postgresql_where=text("cancelled = false"),
            sqlite_where=text("cancelled = 0"),
        ),
    )