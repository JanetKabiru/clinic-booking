# Clinic Booking API

A backend REST API for a small clinic (5 doctors) to manage patient appointment booking, built for the Savannah Informatics backend take-home assessment.

**Live URL:** https://clinic-booking-api-r1yc.onrender.com
**API Docs (Swagger):** https://clinic-booking-api-r1yc.onrender.com/docs

---

## Stack

- **Python 3.13 + FastAPI** - REST API framework
- **SQLAlchemy** - ORM
- **SQLite** (local development) / **PostgreSQL** (production, via Render)
- **pytest** - testing
- **Render** - hosting (web service + managed Postgres)
- **GitHub Actions** - CI/CD

---

## Section 1: Design Decisions

### Slot representation
Slots are **computed on the fly** from each doctor's `work_start`/`work_end`, rather than pre-generated as rows in a `Slot` table.

**Rationale:** Pre-generating slots means storing a row per doctor, per day, per 30-minute block - this grows unnecessarily as the clinic scales (more doctors, more days ahead), and if a doctor's working hours change, all future pre-generated rows become stale and need migrating. Computing on the fly means working hours are a single source of truth on the `Doctor` row; changing them instantly and correctly affects all future availability queries with no migration needed.

### Slot length
Fixed at a 30-minute clinic-wide constant (`SLOT_MINUTES = 30`), per the brief, rather than a configurable per-doctor or per-appointment field.

**Rationale:** The brief states the clinic works in 30-minute slots as a fixed rule. Variable-length appointments would be a reasonable future feature but is out of scope - over-building unrequested flexibility adds complexity without a stated need.

### Data models

**Doctor:** `id`, `name`, `email`, `work_start` (time), `work_end` (time)

**Appointment:** `id`, `doctor_id`, `patient_id`, `slot_time` (datetime, UTC), `cancelled` (bool), `cancellation_reason` (text, nullable)

### Reschedule semantics
Rescheduling **updates the existing Appointment row's `slot_time`** in place, rather than cancelling the old row and creating a new one.

**Rationale:** From the patient's perspective, a rescheduled appointment is the same booking, just moved in time - not a new entity. This also means freeing the old slot and claiming the new one happen as a single atomic `UPDATE` on one row, avoiding a whole class of partial-failure bugs that a two-step delete+create would introduce.

### Timezone handling
All appointment times are stored internally in **UTC**. Naive (timezone-unspecified) input is treated as UTC by explicitly attaching `tzinfo=UTC` rather than shifting the clock time.

**Rationale:** UTC gives every appointment one unambiguous reference point regardless of server location, client timezone, or future multi-branch expansion. Comparisons (e.g., "is this slot in the past?", "is this slot already taken?") are always comparing the same clock. Conversion to local time would only happen at final display - not needed for this assessment's scope.

### Concurrency: preventing double-booking
The core design decision of this project. A partial unique index enforces at the database level:

```sql
UNIQUE (doctor_id, slot_time) WHERE cancelled = FALSE
```

**Rationale:** A "check if slot is free, then insert" pattern in application code is a classic race condition - two concurrent requests can both pass the check before either writes, resulting in a double-booking. The fix moves the check to the database itself: the unique index guarantees only one active (non-cancelled) appointment can exist per doctor/slot combination, no matter how many requests race to book it simultaneously. The `WHERE cancelled = FALSE` condition specifically excludes cancelled rows from the constraint, so a slot correctly becomes re-bookable after cancellation.

In code, this means `book_appointment` and `reschedule_appointment` don't pre-check availability in Python - they attempt the write directly and catch `IntegrityError`, returning `409 Conflict` if the database rejects a duplicate.

### Code structure (service layer)
Business logic (validation, booking, cancellation, rescheduling) lives in `app/services/booking.py`, separate from the FastAPI route handlers in `app/routes/`, and separate from the database models (`app/models.py`) and API request/response schemas (`app/schemas.py`).

**Rationale:** Keeping validation logic out of route handlers means it can be reused identically across `POST /appointments` and `PATCH /appointments/{id}/reschedule` (the brief requires reschedule to validate "as you would for a fresh booking") without duplication, and can be unit tested directly without spinning up HTTP requests. Separating SQLAlchemy models from Pydantic schemas means the API response shape is an explicit allowlist of fields - new database columns (e.g., sensitive fields) don't automatically leak into API responses.

### Authentication
Not implemented in this assessment - the brief does not require it, and no `patient` or `user` authentication model was specified. In a production system, `POST /appointments` and the cancel/reschedule endpoints would need to verify the requester is authorized to act on behalf of the given `patient_id`, to prevent one patient from booking, cancelling, or rescheduling on another's behalf.

---

Project Structure
(venv) PS C:\Users\Administrator\clinic-booking> type README.md
# Clinic Booking API

A backend REST API for a small clinic (5 doctors) to manage patient appointment booking, built for the Savannah Informatics backend take-home assessment.

**Live URL:** https://clinic-booking-api-r1yc.onrender.com
**API Docs (Swagger):** https://clinic-booking-api-r1yc.onrender.com/docs

---

## Stack

- **Python 3.13 + FastAPI** - REST API framework
- **SQLAlchemy** - ORM
- **SQLite** (local development) / **PostgreSQL** (production, via Render)
- **pytest** - testing
- **Render** - hosting (web service + managed Postgres)
- **GitHub Actions** - CI/CD

---

## Section 1: Design Decisions

### Slot representation
Slots are **computed on the fly** from each doctor's `work_start`/`work_end`, rather than pre-generatedas rows in a `Slot` table.

**Rationale:** Pre-generating slots means storing arow per doctor, per day, per 30-minute block - thisgrows unnecessarily as the clinic scales (more doctors, more days ahead), and if a doctor's working hours change, all future pre-generated rows become stale and need migrating. Computing on the fly means working hours are a single source of truth on the `Doctor` row; changing them instantly and correctly affects all future availability queries with no migrationneeded.

### Slot length
Fixed at a 30-minute clinic-wide constant (`SLOT_MINUTES = 30`), per the brief, rather than a configurable per-doctor or per-appointment field.

**Rationale:** The brief states the clinic works in30-minute slots as a fixed rule. Variable-length appointments would be a reasonable future feature but is out of scope - over-building unrequested flexibility adds complexity without a stated need.

### Data models

**Doctor:** `id`, `name`, `email`, `work_start` (time), `work_end` (time)

**Appointment:** `id`, `doctor_id`, `patient_id`, `slot_time` (datetime, UTC), `cancelled` (bool), `cancellation_reason` (text, nullable)

### Reschedule semantics
Rescheduling **updates the existing Appointment row's `slot_time`** in place, rather than cancelling the old row and creating a new one.

**Rationale:** From the patient's perspective, a rescheduled appointment is the same booking, just moved in time - not a new entity. This also means freeing the old slot and claiming the new one happen as a single atomic `UPDATE` on one row, avoiding a whole class of partial-failure bugs that a two-step delete+create would introduce.

### Timezone handling
All appointment times are stored internally in **UTC**. Naive (timezone-unspecified) input is treated as UTC by explicitly attaching `tzinfo=UTC` rather than shifting the clock time.

**Rationale:** UTC gives every appointment one unambiguous reference point regardless of server location, client timezone, or future multi-branch expansion. Comparisons (e.g., "is this slot in the past?", "is this slot already taken?") are always comparing the same clock. Conversion to local time would only happen at final display - not needed for this assessment's scope.

### Concurrency: preventing double-booking
The core design decision of this project. A partialunique index enforces at the database level:

```sql
UNIQUE (doctor_id, slot_time) WHERE cancelled = FALSE
```

**Rationale:** A "check if slot is free, then insert" pattern in application code is a classic race condition - two concurrent requests can both pass the check before either writes, resulting in a double-booking. The fix moves the check to the database itself: the unique index guarantees only one active (non-cancelled) appointment can exist per doctor/slot combination, no matter how many requests race to book itsimultaneously. The `WHERE cancelled = FALSE` condition specifically excludes cancelled rows from the constraint, so a slot correctly becomes re-bookable after cancellation.

In code, this means `book_appointment` and `reschedule_appointment` don't pre-check availability in Python - they attempt the write directly and catch `IntegrityError`, returning `409 Conflict` if the database rejects a duplicate.

### Code structure (service layer)
Business logic (validation, booking, cancellation, rescheduling) lives in `app/services/booking.py`, separate from the FastAPI route handlers in `app/routes/`, and separate from the database models (`app/models.py`) and API request/response schemas (`app/schemas.py`).

**Rationale:** Keeping validation logic out of route handlers means it can be reused identically across`POST /appointments` and `PATCH /appointments/{id}/reschedule` (the brief requires reschedule to validate "as you would for a fresh booking") without duplication, and can be unit tested directly without spinning up HTTP requests. Separating SQLAlchemy models from Pydantic schemas means the API response shape is an explicit allowlist of fields - new database columns (e.g., sensitive fields) don't automatically leak into API responses.

### Authentication
Not implemented in this assessment - the brief doesnot require it, and no `patient` or `user` authentication model was specified. In a production system, `POST /appointments` and the cancel/reschedule endpoints would need to verify the requester is authorized to act on behalf of the given `patient_id`, to prevent one patient from booking, cancelling, or rescheduling on another's behalf.

---

## Project Structure

- `app/main.py` - FastAPI app, startup table creation, demo doctor seed
- `app/database.py` - DB connection/session (SQLite locally, Postgres in production)
- `app/models.py` - SQLAlchemy models: Doctor, Appointment
- `app/schemas.py` - Pydantic request/response schemas
- `app/routes/appointments.py` - POST /appointments, PATCH cancel/reschedule
- `app/routes/doctors.py` - GET /doctors/{id}/availability
- `app/services/booking.py` - Core business logic: validation, booking, cancel, reschedule
- `tests/test_booking.py` - 9 tests covering booking, conflicts, cancel, reschedule, availability

## API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/appointments` | Book a slot |
| GET | `/doctors/{id}/availability?date=YYYY-MM-DD` | List available 30-min slots for a doctor on a date |
| PATCH | `/appointments/{id}/cancel` | Cancel an appointment with a reason |
| PATCH | `/appointments/{id}/reschedule` | Move anappointment to a new slot |
| GET | `/health` | Health check |

Full interactive documentation: `/docs` (Swagger UI).

---

## Running Locally

```bash
git clone https://github.com/JanetKabiru/clinic-booking.git
cd clinic-booking
python -m venv venv
.\venv\Scripts\Activate.ps1        # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --reload-dir app
```

The app creates a local SQLite database (`clinic.db`) automatically on first run, and seeds one demo doctor if none exists (Dr. Jane Otieno, working 09:00-17:00 UTC) - this makes it possible to test the API immediately without a manual seeding step.

Visit `http://127.0.0.1:8000/docs` for interactive API docs.

## Running Tests

```bash
pytest -v
```

9 tests covering: successful booking, double-booking conflict (409), past-slot rejection, working-hoursvalidation, cancellation, double-cancellation rejection, reschedule, rescheduling a cancelled appointment (409), and availability correctly excluding booked slots.

---

## Deployment & CI/CD

**Hosting:** Render (web service + managed PostgreSQL, both free tier)

**Database:** The app reads `DATABASE_URL` from theenvironment; falls back to local SQLite if unset. This means identical code runs in both environments -only the connection string changes.

**Auto-deploy:** Render is connected directly to the `main` branch of this GitHub repository. Every push to `main` automatically triggers a new build and deploy.

**CI pipeline:** `.github/workflows/ci.yml` runs onevery push and pull request targeting `main`. It installs dependencies and runs the full `pytest` suiteon a clean Ubuntu runner - a failing test blocks the workflow (visible as a red X on the PR).

---

## Section 4: AI Reflection

### 1. What did I use AI for across the four sections?

I used AI as a development assistant throughout theproject. It helped me discuss design decisions before implementing them, explain FastAPI and SQLAlchemyconcepts, review my code, troubleshoot errors, and think through different implementation approaches. Istill made the final decisions and tested each feature before considering it complete.

### 2. One example where an AI suggestion improved my work.

While designing the availability feature, I initially considered storing appointment slots in the database. Through discussion with AI, I realized that dynamically generating slots from each doctor's workinghours would avoid stale data if schedules changed and would reduce unnecessary database records. I adopted this approach because it was simpler and easier to maintain.

### 3. One example where AI output was wrong or incomplete, and how I caught it.

During development of the availability endpoint, booked appointments were still appearing as available.The suggested logic looked correct, but the resultswere wrong. By debugging the application and inspecting the datetime values, I discovered that SQLite returned timezone-naive datetimes while my generated slots were timezone-aware. Because the values never matched, booked slots were not being filtered out. After normalizing the datetimes to UTC before comparison, the endpoint behaved correctly. This reinforcedthe importance of testing AI suggestions rather than assuming they are always correct.

### 4. Two decisions I made without AI, and why I trusted my own judgment.

- I decided to keep appointment slots fixed at 30 minutes for the entire clinic. Although configurable appointment durations are possible, the assignment did not require them, and a fixed duration kept the scheduling logic simple and predictable.

- I chose to use SQLite for local development and PostgreSQL for deployment on Render. SQLite made local development quick and lightweight, while PostgreSQL provided a production-ready database environment and better reflected how the application would be deployed in practice.
(venv) PS C:\Users\Administrator\clinic-booking> 

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/appointments` | Book a slot |
| GET | `/doctors/{id}/availability?date=YYYY-MM-DD` | List available 30-min slots for a doctor on a date |
| PATCH | `/appointments/{id}/cancel` | Cancel an appointment with a reason |
| PATCH | `/appointments/{id}/reschedule` | Move an appointment to a new slot |
| GET | `/health` | Health check |

Full interactive documentation: `/docs` (Swagger UI).

---

## Running Locally

```bash
git clone https://github.com/JanetKabiru/clinic-booking.git
cd clinic-booking
python -m venv venv
.\venv\Scripts\Activate.ps1        # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --reload-dir app
```

The app creates a local SQLite database (`clinic.db`) automatically on first run, and seeds one demo doctor if none exists (Dr. Jane Otieno, working 09:00-17:00 UTC) - this makes it possible to test the API immediately without a manual seeding step.

Visit `http://127.0.0.1:8000/docs` for interactive API docs.

## Running Tests

```bash
pytest -v
```

9 tests covering: successful booking, double-booking conflict (409), past-slot rejection, working-hours validation, cancellation, double-cancellation rejection, reschedule, rescheduling a cancelled appointment (409), and availability correctly excluding booked slots.

---

## Deployment & CI/CD

**Hosting:** Render (web service + managed PostgreSQL, both free tier)

**Database:** The app reads `DATABASE_URL` from the environment; falls back to local SQLite if unset. This means identical code runs in both environments - only the connection string changes.

**Auto-deploy:** Render is connected directly to the `main` branch of this GitHub repository. Every push to `main` automatically triggers a new build and deploy.

**CI pipeline:** `.github/workflows/ci.yml` runs on every push and pull request targeting `main`. It installs dependencies and runs the full `pytest` suite on a clean Ubuntu runner - a failing test blocks the workflow (visible as a red X on the PR).

---

## Section 4: AI Reflection

### 1. What did I use AI for across the four sections?

I used AI as a development assistant throughout the project. It helped me discuss design decisions before implementing them, explain FastAPI and SQLAlchemy concepts, review my code, troubleshoot errors, and think through different implementation approaches. I still made the final decisions and tested each feature before considering it complete.

### 2. One example where an AI suggestion improved my work.

While designing the availability feature, I initially considered storing appointment slots in the database. Through discussion with AI, I realized that dynamically generating slots from each doctor's working hours would avoid stale data if schedules changed and would reduce unnecessary database records. I adopted this approach because it was simpler and easier to maintain.

### 3. One example where AI output was wrong or incomplete, and how I caught it.

During development of the availability endpoint, booked appointments were still appearing as available. The suggested logic looked correct, but the results were wrong. By debugging the application and inspecting the datetime values, I discovered that SQLite returned timezone-naive datetimes while my generated slots were timezone-aware. Because the values never matched, booked slots were not being filtered out. After normalizing the datetimes to UTC before comparison, the endpoint behaved correctly. This reinforced the importance of testing AI suggestions rather than assuming they are always correct.

### 4. Two decisions I made without AI, and why I trusted my own judgment.

- I decided to keep appointment slots fixed at 30 minutes for the entire clinic. Although configurable appointment durations are possible, the assignment did not require them, and a fixed duration kept the scheduling logic simple and predictable.

- I chose to use SQLite for local development and PostgreSQL for deployment on Render. SQLite made local development quick and lightweight, while PostgreSQL provided a production-ready database environment and better reflected how the application would be deployed in practice.