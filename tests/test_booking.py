from datetime import datetime, timedelta, time

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app import models
from fastapi.testclient import TestClient

TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_and_teardown():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    doctor = models.Doctor(
        name="Dr. Test",
        email="dr.test@example.com",
        work_start=time(9, 0),
        work_end=time(17, 0),
    )
    db.add(doctor)
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


def future_slot(hour=10, days_ahead=1):
    target = datetime.now() + timedelta(days=days_ahead)
    return target.replace(hour=hour, minute=0, second=0, microsecond=0).isoformat()


def test_book_appointment_success():
    response = client.post(
        "/appointments",
        json={"doctor_id": 1, "patient_id": 1, "slot_time": future_slot()},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["doctor_id"] == 1
    assert body["cancelled"] is False


def test_book_same_slot_twice_returns_409():
    slot = future_slot(hour=11)
    client.post("/appointments", json={"doctor_id": 1, "patient_id": 1, "slot_time": slot})
    response = client.post(
        "/appointments", json={"doctor_id": 1, "patient_id": 2, "slot_time": slot}
    )
    assert response.status_code == 409


def test_book_past_slot_returns_400():
    past = (datetime.now() - timedelta(days=1)).replace(hour=10, minute=0).isoformat()
    response = client.post(
        "/appointments", json={"doctor_id": 1, "patient_id": 1, "slot_time": past}
    )
    assert response.status_code == 400


def test_book_outside_working_hours_returns_400():
    response = client.post(
        "/appointments",
        json={"doctor_id": 1, "patient_id": 1, "slot_time": future_slot(hour=20)},
    )
    assert response.status_code == 400


def test_cancel_appointment_success():
    slot = future_slot(hour=12)
    booked = client.post(
        "/appointments", json={"doctor_id": 1, "patient_id": 1, "slot_time": slot}
    )
    appointment_id = booked.json()["id"]

    response = client.patch(
        f"/appointments/{appointment_id}/cancel", json={"reason": "Test cancellation"}
    )
    assert response.status_code == 200
    assert response.json()["cancelled"] is True


def test_cancel_already_cancelled_returns_409():
    slot = future_slot(hour=13)
    booked = client.post(
        "/appointments", json={"doctor_id": 1, "patient_id": 1, "slot_time": slot}
    )
    appointment_id = booked.json()["id"]
    client.patch(f"/appointments/{appointment_id}/cancel", json={"reason": "First cancel"})

    response = client.patch(
        f"/appointments/{appointment_id}/cancel", json={"reason": "Second cancel"}
    )
    assert response.status_code == 409


def test_reschedule_appointment_success():
    slot = future_slot(hour=14)
    booked = client.post(
        "/appointments", json={"doctor_id": 1, "patient_id": 1, "slot_time": slot}
    )
    appointment_id = booked.json()["id"]

    new_slot = future_slot(hour=15)
    response = client.patch(
        f"/appointments/{appointment_id}/reschedule",
        json={"new_slot_time": new_slot},
    )
    assert response.status_code == 200
    assert response.json()["slot_time"].startswith(new_slot[:16])


def test_reschedule_cancelled_appointment_returns_409():
    slot = future_slot(hour=16)
    booked = client.post(
        "/appointments", json={"doctor_id": 1, "patient_id": 1, "slot_time": slot}
    )
    appointment_id = booked.json()["id"]
    client.patch(f"/appointments/{appointment_id}/cancel", json={"reason": "Cancel first"})

    response = client.patch(
        f"/appointments/{appointment_id}/reschedule",
        json={"new_slot_time": future_slot(hour=17)},
    )
    assert response.status_code == 409


def test_availability_excludes_booked_slot():
    slot = future_slot(hour=10, days_ahead=2)
    client.post("/appointments", json={"doctor_id": 1, "patient_id": 1, "slot_time": slot})

    target_date = slot[:10]
    response = client.get(f"/doctors/1/availability?date={target_date}")
    assert response.status_code == 200
    slot_times = [s["slot_time"] for s in response.json()]
    assert not any(t.startswith(slot[:16]) for t in slot_times)