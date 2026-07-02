import json
import re
from datetime import datetime

from app.database.db import get_db
from app.database.models import Appointment, Doctor, Patient
from app.utils.helpers import format_appointment, parse_datetime


def get_available_slots(doctor_id: int) -> list[str]:
    with get_db() as session:
        doctor = session.get(Doctor, doctor_id)
        if not doctor:
            return []
        return json.loads(doctor.available_slots)


def book_appointment(
    patient_id: int,
    doctor_id: int,
    slot: str,
    notes: str = "",
    booked_via: str = "manual",
) -> dict:
    appointment_time = parse_datetime(slot)
    if appointment_time is None:
        return {"success": False, "error": "Invalid datetime format. Use YYYY-MM-DD HH:MM"}

    with get_db() as session:
        doctor = session.get(Doctor, doctor_id)
        patient = session.get(Patient, patient_id)
        if not doctor or not patient:
            return {"success": False, "error": "Doctor or patient not found"}

        slots = json.loads(doctor.available_slots)
        if slot not in slots:
            return {"success": False, "error": f"Slot {slot} not available for Dr. {doctor.name}"}

        existing = (
            session.query(Appointment)
            .filter(
                Appointment.doctor_id == doctor_id,
                Appointment.datetime == appointment_time,
                Appointment.status == "scheduled",
            )
            .first()
        )
        if existing:
            return {"success": False, "error": "This slot is already booked"}

        slots.remove(slot)
        doctor.available_slots = json.dumps(slots)

        appointment = Appointment(
            patient_id=patient_id,
            doctor_id=doctor_id,
            datetime=appointment_time,
            status="scheduled",
            notes=notes,
            booked_via=booked_via,
        )
        session.add(appointment)
        session.flush()

        result = {
            "success": True,
            "appointment": {
                "id": appointment.id,
                "patient_name": patient.name,
                "doctor_name": doctor.name,
                "datetime": appointment_time.strftime("%Y-%m-%d %H:%M"),
                "status": appointment.status,
                "booked_via": booked_via,
            },
        }

        from app.services.notification_service import schedule_appointment_reminders

        result["reminders"] = schedule_appointment_reminders(
            appointment.id,
            appointment_time,
            doctor.name,
            session=session,
        )
        return result


def cancel_appointment(appointment_id: int) -> dict:
    with get_db() as session:
        appointment = session.get(Appointment, appointment_id)
        if not appointment:
            return {"success": False, "error": "Appointment not found"}
        appointment.status = "cancelled"
        return {"success": True, "appointment_id": appointment_id}


def list_patient_appointments(patient_id: int) -> list[dict]:
    with get_db() as session:
        rows = (
            session.query(Appointment)
            .filter(Appointment.patient_id == patient_id)
            .order_by(Appointment.datetime)
            .all()
        )
        results = []
        for row in rows:
            results.append(
                {
                    "id": row.id,
                    "patient_name": row.patient.name,
                    "doctor_name": row.doctor.name,
                    "datetime": row.datetime.strftime("%Y-%m-%d %H:%M"),
                    "status": row.status,
                }
            )
        return results


def run_scheduling(message: str, patient_id: int = 1) -> str:
    if "cancel" in message.lower():
        match = re.search(r"#?(\d+)", message)
        if match:
            result = cancel_appointment(int(match.group(1)))
            if result["success"]:
                return f"Appointment #{result['appointment_id']} has been cancelled."
            return result["error"]
        return "Please provide an appointment ID to cancel (e.g., 'cancel appointment #1')."

    doctor_match = re.search(r"dr\.?\s*(\w+)", message, re.IGNORECASE)
    slot_match = re.search(r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})", message)

    with get_db() as session:
        if doctor_match:
            name_part = doctor_match.group(1)
            doctor = (
                session.query(Doctor)
                .filter(Doctor.name.ilike(f"%{name_part}%"))
                .first()
            )
        else:
            doctor = session.query(Doctor).first()

        if not doctor:
            return "I couldn't find that doctor. Please specify Dr. <name> and a slot."

        if not slot_match:
            slots = json.loads(doctor.available_slots)
            slot_list = ", ".join(slots) if slots else "No slots available"
            return (
                f"Available slots for Dr. {doctor.name}:\n{slot_list}\n\n"
                "Reply with: Book Dr. <name> on YYYY-MM-DD HH:MM"
            )

        result = book_appointment(patient_id, doctor.id, slot_match.group(1))
        if result["success"]:
            return f"Booked successfully!\n{format_appointment(result['appointment'])}"
        return result["error"]
