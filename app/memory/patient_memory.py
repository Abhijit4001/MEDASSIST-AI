import json

from app.database.db import get_db
from app.database.models import Patient
from app.memory.chroma_store import add_memory, query_memory


def store_interaction(patient_id: int, message: str, response: str) -> None:
    text = f"Patient: {message}\nAssistant: {response}"
    add_memory(patient_id, text, {"type": "chat"})


def get_patient_context(patient_id: int, query: str) -> str:
    memories = query_memory(patient_id, query)
    if not memories:
        return ""
    return "Recent context:\n" + "\n".join(f"- {m}" for m in memories)


def get_patient_profile(patient_id: int) -> dict | None:
    with get_db() as session:
        patient = session.get(Patient, patient_id)
        if not patient:
            return None
        return {
            "id": patient.id,
            "name": patient.name,
            "email": patient.email,
            "phone": patient.phone,
            "date_of_birth": patient.date_of_birth,
            "medical_history": json.loads(patient.medical_history),
            "allergies": json.loads(patient.allergies),
        }
