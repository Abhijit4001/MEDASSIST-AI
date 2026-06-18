import json

from app.database.db import get_db
from app.database.models import Patient
from app.memory.patient_memory import get_patient_context, get_patient_profile


def get_records(patient_id: int) -> dict | None:
    return get_patient_profile(patient_id)


def update_medical_history(patient_id: int, entry: str) -> dict:
    with get_db() as session:
        patient = session.get(Patient, patient_id)
        if not patient:
            return {"success": False, "error": "Patient not found"}
        history = json.loads(patient.medical_history)
        if entry not in history:
            history.append(entry)
        patient.medical_history = json.dumps(history)
        return {"success": True, "medical_history": history}


def run_patient_records(message: str, patient_id: int = 1) -> str:
    profile = get_records(patient_id)
    if not profile:
        return "Patient record not found."

    if "add" in message.lower() or "update" in message.lower():
        entry = message.split(":", 1)[-1].strip()
        if len(entry) < 5:
            return "Please provide a medical history entry after a colon, e.g., 'add history: mild asthma'"
        result = update_medical_history(patient_id, entry)
        return f"Updated medical history: {', '.join(result['medical_history'])}"

    context = get_patient_context(patient_id, message)
    allergies = ", ".join(profile["allergies"]) or "None"
    history = ", ".join(profile["medical_history"]) or "None"

    return (
        f"**Patient Record — {profile['name']}**\n"
        f"- Email: {profile['email']}\n"
        f"- Phone: {profile['phone']}\n"
        f"- DOB: {profile['date_of_birth']}\n"
        f"- Medical History: {history}\n"
        f"- Allergies: {allergies}\n"
        f"\n{context}"
    ).strip()
