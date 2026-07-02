from datetime import datetime

from app.agents.scheduling_agent import list_patient_appointments
from app.services.notification_service import get_sent_reminders, list_appointment_reminders, schedule_reminder
from app.database.db import get_db
from app.database.models import Appointment


def run_reminder(message: str, patient_id: int = 1) -> str:
    appointments = list_patient_appointments(patient_id)
    upcoming = [a for a in appointments if a["status"] == "scheduled"]

    if not upcoming:
        return "You have no upcoming appointments to remind you about."

    if "set" in message.lower() or "remind" in message.lower():
        appt = upcoming[0]
        with get_db() as session:
            row = session.get(Appointment, appt["id"])
            if row:
                result = schedule_reminder(
                    row.id,
                    row.patient.email,
                    row.doctor.name,
                    row.datetime,
                )
                reminders = result.get("reminders", [])
                if reminders:
                    lines = [f"Scheduled {len(reminders)} reminder(s) for appointment #{appt['id']}:"]
                    for item in reminders:
                        lines.append(f"- {item['remind_at'][:16].replace('T', ' ')} ({item['type'].replace('_', ' ')})")
                    return "\n".join(lines)
                return "No future reminder windows are available for this appointment yet."

    lines = ["Your upcoming appointments:"]
    for appt in upcoming:
        lines.append(f"- #{appt['id']}: Dr. {appt['doctor_name']} on {appt['datetime']}")
    lines.append("\nSay 'set reminder' to schedule an email reminder.")
    return "\n".join(lines)


def reminder_status() -> list[dict]:
    return get_sent_reminders()
