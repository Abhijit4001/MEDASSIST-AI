from app.database.db import get_db
from app.database.models import Appointment
from app.services.gemini_service import generate_text
from app.utils.prompts import VISIT_SUMMARY_SYSTEM


def generate_visit_summary(appointment_id: int) -> dict:
    with get_db() as session:
        appointment = session.get(Appointment, appointment_id)
        if not appointment:
            return {"success": False, "error": "Appointment not found"}

        notes = appointment.notes or "No detailed notes provided."
        patient_name = appointment.patient.name
        doctor_name = appointment.doctor.name
        appt_date = appointment.datetime.strftime("%Y-%m-%d")

        prompt = (
            f"Patient: {patient_name}\n"
            f"Doctor: Dr. {doctor_name}\n"
            f"Date: {appt_date}\n"
            f"Notes: {notes}"
        )
        summary = generate_text(prompt, VISIT_SUMMARY_SYSTEM)
        if not summary:
            summary = (
                f"Visit Summary — {appt_date}\n"
                f"Patient: {patient_name} | Provider: Dr. {doctor_name}\n"
                f"Chief Complaint: {notes}\n"
                f"Assessment: Patient evaluated; follow standard care plan.\n"
                f"Follow-up: As recommended by Dr. {doctor_name}."
            )

        appointment.visit_summary = summary
        appointment.status = "completed"
        return {
            "success": True,
            "appointment_id": appointment_id,
            "summary": summary,
        }


def run_visit_summary(message: str) -> str:
    import re

    match = re.search(r"#?(\d+)", message)
    if not match:
        return "Please provide an appointment ID, e.g., 'summary for appointment #1'."

    result = generate_visit_summary(int(match.group(1)))
    if not result["success"]:
        return result["error"]
    return f"**Visit Summary**\n\n{result['summary']}"
