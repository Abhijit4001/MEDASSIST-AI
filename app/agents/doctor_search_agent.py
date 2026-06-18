import json

from app.database.db import get_db
from app.database.models import Doctor
from app.services.gemini_service import generate_text
from app.utils.helpers import format_doctor_card, normalize_text
from app.utils.prompts import DOCTOR_SEARCH_SYSTEM


def search_doctors(
    specialty: str | None = None,
    location: str | None = None,
    name: str | None = None,
) -> list[dict]:
    with get_db() as session:
        doctors = session.query(Doctor).all()
        results = []
        for doc in doctors:
            if specialty and normalize_text(specialty) not in normalize_text(doc.specialty):
                continue
            if location and normalize_text(location) not in normalize_text(doc.location):
                continue
            if name and normalize_text(name) not in normalize_text(doc.name):
                continue
            results.append(
                {
                    "id": doc.id,
                    "name": doc.name,
                    "specialty": doc.specialty,
                    "hospital": doc.hospital,
                    "location": doc.location,
                    "rating": doc.rating,
                    "email": doc.email,
                    "available_slots": json.loads(doc.available_slots),
                }
            )
    return sorted(results, key=lambda d: d["rating"], reverse=True)


def run_doctor_search(message: str) -> str:
    specialty = _extract_term(message, ["cardiology", "dermatology", "pediatrics", "orthopedics", "physician", "general"])
    location = _extract_term(message, ["mumbai", "delhi", "bangalore", "pune"])
    name = _extract_doctor_name(message)

    doctors = search_doctors(specialty=specialty, location=location, name=name)
    if not doctors:
        return (
            "I couldn't find doctors matching your criteria. "
            "Try searching by specialty (e.g., cardiology) or city (e.g., Mumbai)."
        )

    cards = "\n\n".join(format_doctor_card(d) for d in doctors[:5])
    ai_note = generate_text(
        f"Query: {message}\nDoctors: {json.dumps(doctors[:3])}",
        DOCTOR_SEARCH_SYSTEM,
    )
    header = f"Found {len(doctors)} doctor(s):\n\n{cards}"
    return f"{header}\n\n{ai_note}" if ai_note else header


def _extract_term(message: str, terms: list[str]) -> str | None:
    lower = normalize_text(message)
    for term in terms:
        if term in lower:
            return term.title() if term != "physician" else "General Physician"
    return None


def _extract_doctor_name(message: str) -> str | None:
    lower = normalize_text(message)
    if "dr." in lower or "doctor" in lower:
        words = message.replace("Dr.", "").replace("dr.", "").replace("doctor", "").strip().split()
        if words:
            return words[0]
    return None
