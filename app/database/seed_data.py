import json
from datetime import datetime, timedelta

from app.database.db import get_db, init_db
from app.database.models import Appointment, Doctor, Patient
from app.utils.constants import DATA_DIR

SAMPLE_DOCTORS = [
    {
        "name": "Ananya Sharma",
        "specialty": "Cardiology",
        "hospital": "City Heart Institute",
        "location": "Mumbai",
        "rating": 4.8,
        "email": "ananya.sharma@cityheart.in",
        "available_slots": ["2026-06-12 10:00", "2026-06-12 14:00", "2026-06-13 09:00"],
    },
    {
        "name": "Rahul Mehta",
        "specialty": "Dermatology",
        "hospital": "SkinCare Clinic",
        "location": "Delhi",
        "rating": 4.6,
        "email": "rahul.mehta@skincare.in",
        "available_slots": ["2026-06-12 11:00", "2026-06-14 15:00"],
    },
    {
        "name": "Priya Nair",
        "specialty": "Pediatrics",
        "hospital": "Children's Wellness Center",
        "location": "Bangalore",
        "rating": 4.9,
        "email": "priya.nair@kidshealth.in",
        "available_slots": ["2026-06-12 09:30", "2026-06-13 16:00"],
    },
    {
        "name": "Vikram Singh",
        "specialty": "Orthopedics",
        "hospital": "Bone & Joint Hospital",
        "location": "Mumbai",
        "rating": 4.5,
        "email": "vikram.singh@bonejoint.in",
        "available_slots": ["2026-06-15 10:00", "2026-06-15 12:00"],
    },
    {
        "name": "Meera Kapoor",
        "specialty": "General Physician",
        "hospital": "Metro Health",
        "location": "Pune",
        "rating": 4.4,
        "email": "meera.kapoor@metrohealth.in",
        "available_slots": ["2026-06-12 08:00", "2026-06-12 17:00"],
    },
]

SAMPLE_PATIENTS = [
    {
        "name": "Arjun Patel",
        "email": "arjun.patel@email.com",
        "phone": "+91-9876543210",
        "date_of_birth": "1990-05-15",
        "medical_history": ["Hypertension (controlled)", "Seasonal allergies"],
        "allergies": ["Penicillin"],
    },
    {
        "name": "Sneha Reddy",
        "email": "sneha.reddy@email.com",
        "phone": "+91-9123456789",
        "date_of_birth": "1985-11-22",
        "medical_history": ["Type 2 Diabetes"],
        "allergies": [],
    },
]


def _export_json() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with get_db() as session:
        doctors = session.query(Doctor).all()
        patients = session.query(Patient).all()
        appointments = session.query(Appointment).all()

        doctors_data = [
            {
                "id": d.id,
                "name": d.name,
                "specialty": d.specialty,
                "hospital": d.hospital,
                "location": d.location,
                "rating": d.rating,
                "email": d.email,
                "available_slots": json.loads(d.available_slots),
            }
            for d in doctors
        ]
        patients_data = [
            {
                "id": p.id,
                "name": p.name,
                "email": p.email,
                "phone": p.phone,
                "date_of_birth": p.date_of_birth,
                "medical_history": json.loads(p.medical_history),
                "allergies": json.loads(p.allergies),
            }
            for p in patients
        ]
        appointments_data = [
            {
                "id": a.id,
                "patient_id": a.patient_id,
                "doctor_id": a.doctor_id,
                "datetime": a.datetime.strftime("%Y-%m-%d %H:%M"),
                "status": a.status,
                "notes": a.notes,
                "visit_summary": a.visit_summary,
            }
            for a in appointments
        ]

    (DATA_DIR / "doctors.json").write_text(json.dumps(doctors_data, indent=2))
    (DATA_DIR / "patients.json").write_text(json.dumps(patients_data, indent=2))
    (DATA_DIR / "appointments.json").write_text(json.dumps(appointments_data, indent=2))


def seed_database(force: bool = False) -> None:
    init_db()
    with get_db() as session:
        if not force and session.query(Doctor).count() > 0:
            return

        if force:
            session.query(Appointment).delete()
            session.query(Patient).delete()
            session.query(Doctor).delete()

        for doc in SAMPLE_DOCTORS:
            session.add(
                Doctor(
                    name=doc["name"],
                    specialty=doc["specialty"],
                    hospital=doc["hospital"],
                    location=doc["location"],
                    rating=doc["rating"],
                    email=doc["email"],
                    available_slots=json.dumps(doc["available_slots"]),
                )
            )
        session.flush()

        for pat in SAMPLE_PATIENTS:
            session.add(
                Patient(
                    name=pat["name"],
                    email=pat["email"],
                    phone=pat["phone"],
                    date_of_birth=pat["date_of_birth"],
                    medical_history=json.dumps(pat["medical_history"]),
                    allergies=json.dumps(pat["allergies"]),
                )
            )
        session.flush()

        doctor = session.query(Doctor).first()
        patient = session.query(Patient).first()
        if doctor and patient:
            session.add(
                Appointment(
                    patient_id=patient.id,
                    doctor_id=doctor.id,
                    datetime=datetime.now() + timedelta(days=2),
                    status="scheduled",
                    notes="Routine cardiac checkup",
                )
            )

    _export_json()


if __name__ == "__main__":
    seed_database(force=True)
    print("Database seeded successfully.")
