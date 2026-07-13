from datetime import time
from app.database import SessionLocal
from app import models

db = SessionLocal()

doctor = models.Doctor(
    name="Dr. Jane Otieno",
    email="jane.otieno@example.com",
    work_start=time(9, 0),
    work_end=time(17, 0),
)
db.add(doctor)
db.commit()
db.refresh(doctor)

print(f"Created doctor with id={doctor.id}")

db.close()