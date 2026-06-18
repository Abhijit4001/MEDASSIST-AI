from app.agents.doctor_search_agent import run_doctor_search
from app.agents.patient_record_agent import run_patient_records
from app.agents.reminder_agent import run_reminder
from app.agents.scheduling_agent import run_scheduling
from app.agents.visit_summary_agent import run_visit_summary
from app.services.gemini_service import classify_intent, generate_text
from app.utils.constants import (
    INTENT_BOOK,
    INTENT_GENERAL,
    INTENT_RECORDS,
    INTENT_REMINDER,
    INTENT_SEARCH,
    INTENT_SUMMARY,
)
from app.utils.helpers import normalize_text
from app.utils.prompts import GENERAL_SYSTEM


def detect_intent(message: str) -> str:
    ai_intent = classify_intent(message)
    if ai_intent:
        return ai_intent

    text = normalize_text(message)
    if any(w in text for w in ("summary", "visit report", "discharge")):
        return INTENT_SUMMARY
    if any(w in text for w in ("find doctor", "search doctor", "cardiolog", "dermatolog", "pediatr", "orthoped", "specialist")):
        return INTENT_SEARCH
    if any(w in text for w in ("book", "schedule", "cancel")) or (
        "appointment" in text and "summary" not in text
    ):
        return INTENT_BOOK
    if any(w in text for w in ("record", "history", "allerg", "medical")):
        return INTENT_RECORDS
    if any(w in text for w in ("remind", "reminder", "notify")):
        return INTENT_REMINDER
    return INTENT_GENERAL


def route_message(message: str, patient_id: int = 1) -> dict:
    intent = detect_intent(message)

    handlers = {
        INTENT_SEARCH: lambda: run_doctor_search(message),
        INTENT_BOOK: lambda: run_scheduling(message, patient_id),
        INTENT_RECORDS: lambda: run_patient_records(message, patient_id),
        INTENT_REMINDER: lambda: run_reminder(message, patient_id),
        INTENT_SUMMARY: lambda: run_visit_summary(message),
    }

    if intent in handlers:
        response = handlers[intent]()
    else:
        response = generate_text(message, GENERAL_SYSTEM)
        if not response:
            response = (
                "Hello! I'm MedAssist AI. I can help you:\n"
                "- Find doctors by specialty or location\n"
                "- Book or cancel appointments\n"
                "- View your medical records\n"
                "- Set appointment reminders\n"
                "- Generate visit summaries"
            )

    return {"intent": intent, "response": response, "patient_id": patient_id}
