import sqlite3

conn = sqlite3.connect("clinic.db")

print("Doctors:")
for row in conn.execute("SELECT id, name, email, work_start, work_end FROM doctors"):
    print(row)

print("\nAppointments:")
for row in conn.execute("SELECT id, doctor_id, patient_id, slot_time, cancelled FROM appointments"):
    print(row)