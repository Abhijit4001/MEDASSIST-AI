import json
import re
from datetime import datetime

from app.agents.doctor_search_agent import search_doctors
from app.agents.scheduling_agent import book_appointment
from app.database.db import get_db
from app.database.models import CallSession, Doctor, Patient
from app.services.gemini_service import generate_text, is_gemini_available
from app.services.notification_service import list_appointment_reminders
from app.utils.helpers import normalize_text
from app.utils.prompts import CALL_AGENT_SYSTEM


def _load_transcript(session: CallSession) -> list[dict]:
    try:
        return json.loads(session.transcript or "[]")
    except json.JSONDecodeError:
        return []


def _save_transcript(session: CallSession, transcript: list[dict]) -> None:
    session.transcript = json.dumps(transcript)


def _append_turn(session: CallSession, speaker: str, text: str) -> list[dict]:
    transcript = _load_transcript(session)
    transcript.append({"speaker": speaker, "text": text, "at": datetime.now().isoformat()})
    _save_transcript(session, transcript)
    return transcript


def _doctor_payload(doctor: Doctor) -> dict:
    return {
        "id": doctor.id,
        "name": doctor.name,
        "specialty": doctor.specialty,
        "location": doctor.location,
        "rating": doctor.rating,
        "available_slots": json.loads(doctor.available_slots),
    }


def _match_doctor(message: str, doctors: list[dict]) -> dict | None:
    text = normalize_text(message)
    for doctor in doctors:
        parts = normalize_text(doctor["name"]).split()
        if any(part in text for part in parts if len(part) > 2):
            return doctor
    number_match = re.search(r"\b([1-9])\b", text)
    if number_match:
        index = int(number_match.group(1)) - 1
        if 0 <= index < len(doctors):
            return doctors[index]
    return None


def _match_slot(message: str, slots: list[str]) -> str | None:
    slot_match = re.search(r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})", message)
    if slot_match:
        return slot_match.group(1)
    text = normalize_text(message)
    if "first" in text and slots:
        return slots[0]
    if "second" in text and len(slots) > 1:
        return slots[1]
    for slot in slots:
        if normalize_text(slot) in text:
            return slot
    return None


def _extract_specialty(message: str) -> str | None:
    keywords = {
        "cardio": "Cardiology",
        "dermat": "Dermatology",
        "pediatr": "Pediatrics",
        "orthoped": "Orthopedics",
        "physician": "General Physician",
        "general": "General Physician",
    }
    text = normalize_text(message)
    for key, specialty in keywords.items():
        if key in text:
            return specialty
    return None


def _extract_location(message: str) -> str | None:
    cities = ["mumbai", "delhi", "bangalore", "pune"]
    text = normalize_text(message)
    for city in cities:
        if city in text:
            return city.title()
    return None


def _format_doctor_options(doctors: list[dict]) -> str:
    lines = []
    for index, doctor in enumerate(doctors[:3], start=1):
        lines.append(
            f"{index}. Dr. {doctor['name']} ({doctor['specialty']}, {doctor['location']}, "
            f"rating {doctor['rating']}/5)"
        )
    return "\n".join(lines)


def _format_slot_options(slots: list[str]) -> str:
    return "\n".join(f"{index + 1}. {slot}" for index, slot in enumerate(slots[:4]))


def _serialize_call(session: CallSession, extra: dict | None = None) -> dict:
    payload = {
        "id": session.id,
        "patient_id": session.patient_id,
        "status": session.status,
        "stage": session.stage,
        "selected_doctor_id": session.selected_doctor_id,
        "selected_slot": session.selected_slot,
        "appointment_id": session.appointment_id,
        "transcript": _load_transcript(session),
        "created_at": session.created_at.isoformat(),
        "completed_at": session.completed_at.isoformat() if session.completed_at else None,
    }
    if extra:
        payload.update(extra)
    return payload


def start_call(patient_id: int) -> dict:
    with get_db() as session:
        patient = session.get(Patient, patient_id)
        if not patient:
            return {"success": False, "error": "Patient not found"}

        call = CallSession(patient_id=patient_id, stage="collecting_need", status="active")
        session.add(call)
        session.flush()

        greeting = (
            f"Hello {patient.name}, this is MedAssist AI calling on behalf of your care team. "
            "I can help you book an appointment right now. "
            "What kind of doctor would you like to see, and which city works best for you?"
        )
        _append_turn(call, "ai", greeting)
        return {"success": True, "call": _serialize_call(call), "ai_message": greeting}


def process_call_turn(call_id: int, patient_message: str) -> dict:
    patient_message = patient_message.strip()
    if not patient_message:
        return {"success": False, "error": "Patient message is required"}

    with get_db() as session:
        call = session.get(CallSession, call_id)
        if not call or call.status != "active":
            return {"success": False, "error": "Call session not found or already completed"}

        patient = session.get(Patient, call.patient_id)
        _append_turn(call, "patient", patient_message)

        if is_gemini_available():
            result = _process_with_gemini(session, call, patient, patient_message)
        else:
            result = _process_with_rules(session, call, patient, patient_message)

        if result.get("ai_message"):
            _append_turn(call, "ai", result["ai_message"])

        return {
            "success": True,
            "call": _serialize_call(call, result.get("extra")),
            "ai_message": result.get("ai_message", ""),
            "booked": result.get("booked", False),
            "reminders": result.get("reminders", []),
        }


def _process_with_rules(session, call: CallSession, patient: Patient, patient_message: str) -> dict:
    text = normalize_text(patient_message)

    if call.stage == "collecting_need":
        specialty = _extract_specialty(patient_message)
        location = _extract_location(patient_message)
        doctors = search_doctors(specialty=specialty, location=location)
        if not doctors:
            doctors = search_doctors(specialty=specialty) or search_doctors(location=location)
        if not doctors:
            return {
                "ai_message": "I couldn't find a matching doctor yet. Could you share the specialty and city again?",
            }

        call.stage = "selecting_doctor"
        options = _format_doctor_options(doctors)
        return {
            "ai_message": (
                f"Thanks {patient.name}. I found these doctors:\n{options}\n"
                "Which doctor would you like? You can say the doctor's name or option number."
            ),
            "extra": {"doctor_options": doctors[:3]},
        }

    if call.stage == "selecting_doctor":
        doctors = search_doctors()
        if call.selected_doctor_id:
            selected = next((d for d in doctors if d["id"] == call.selected_doctor_id), None)
        else:
            selected = _match_doctor(patient_message, doctors[:10])
        if not selected:
            return {"ai_message": "Please choose one of the listed doctors by name or number."}

        call.selected_doctor_id = selected["id"]
        slots = selected["available_slots"]
        if not slots:
            return {"ai_message": f"Dr. {selected['name']} has no open slots right now. Would you like another doctor?"}

        call.stage = "selecting_slot"
        return {
            "ai_message": (
                f"Great choice. Dr. {selected['name']} has these open slots:\n"
                f"{_format_slot_options(slots)}\nWhich slot should I book?"
            ),
            "extra": {"slot_options": slots[:4]},
        }

    if call.stage == "selecting_slot":
        doctor = session.get(Doctor, call.selected_doctor_id) if call.selected_doctor_id else None
        if not doctor:
            call.stage = "collecting_need"
            return {"ai_message": "Let's start again. Which specialty and city do you need?"}

        slots = json.loads(doctor.available_slots)
        slot = _match_slot(patient_message, slots)
        if not slot:
            return {
                "ai_message": (
                    f"I didn't catch the slot. Available times are:\n{_format_slot_options(slots)}\n"
                    "Please repeat the date and time."
                ),
            }

        call.selected_slot = slot
        call.stage = "confirming"
        return {
            "ai_message": (
                f"Perfect. I can book Dr. {doctor.name} on {slot} for you. "
                "Should I confirm this appointment?"
            ),
        }

    if call.stage == "confirming":
        if any(word in text for word in ("yes", "confirm", "book", "okay", "ok", "sure")):
            return _finalize_booking(session, call, patient, "Booked through AI phone call")
        if any(word in text for word in ("no", "cancel", "change")):
            call.stage = "collecting_need"
            call.selected_doctor_id = None
            call.selected_slot = ""
            return {"ai_message": "No problem. Let's pick a different doctor. What specialty do you need?"}
        return {"ai_message": "Please say yes to confirm the booking or no to choose another slot."}

    return {"ai_message": "I'm here to help you book an appointment. What specialty are you looking for?"}


def _process_with_gemini(session, call: CallSession, patient: Patient, patient_message: str) -> dict:
    doctors = search_doctors()
    selected_doctor = None
    if call.selected_doctor_id:
        selected_doctor = next((d for d in doctors if d["id"] == call.selected_doctor_id), None)

    prompt = (
        f"Patient name: {patient.name}\n"
        f"Current stage: {call.stage}\n"
        f"Selected doctor: {json.dumps(selected_doctor)}\n"
        f"Selected slot: {call.selected_slot}\n"
        f"Doctors: {json.dumps(doctors[:5])}\n"
        f"Patient just said: {patient_message}\n"
        f"Transcript: {call.transcript}"
    )
    raw = generate_text(prompt, CALL_AGENT_SYSTEM)
    try:
        payload = json.loads(raw.strip().strip("`").replace("json", "", 1))
    except json.JSONDecodeError:
        return _process_with_rules(session, call, patient, patient_message)

    call.stage = payload.get("stage", call.stage)
    if payload.get("selected_doctor_id"):
        call.selected_doctor_id = int(payload["selected_doctor_id"])
    if payload.get("selected_slot"):
        call.selected_slot = payload["selected_slot"]

    if payload.get("book_now") and call.selected_doctor_id and call.selected_slot:
        return _finalize_booking(session, call, patient, "Booked through AI phone call")

    return {"ai_message": payload.get("speech", "Could you repeat that?")}


def _finalize_booking(session, call: CallSession, patient: Patient, notes: str) -> dict:
    booking = book_appointment(
        patient_id=patient.id,
        doctor_id=call.selected_doctor_id,
        slot=call.selected_slot,
        notes=notes,
        booked_via="ai_call",
    )
    if not booking["success"]:
        return {"ai_message": booking["error"]}

    appointment = booking["appointment"]
    reminders = booking.get("reminders") or list_appointment_reminders(appointment["id"])

    call.status = "completed"
    call.stage = "completed"
    call.appointment_id = appointment["id"]
    call.completed_at = datetime.now()

    reminder_lines = [
        f"- {item['remind_at'][:16].replace('T', ' ')} ({item['type'].replace('_', ' ')})"
        for item in reminders
    ]
    reminder_text = "\n".join(reminder_lines) if reminder_lines else "- Reminders will be scheduled close to the appointment date."

    return {
        "booked": True,
        "reminders": reminders,
        "ai_message": (
            f"Done. Your appointment with Dr. {appointment['doctor_name']} is confirmed for "
            f"{appointment['datetime']}. I've scheduled reminders for:\n{reminder_text}\n"
            "Thank you for booking with MedAssist AI."
        ),
    }


def get_call_session(call_id: int) -> dict | None:
    with get_db() as session:
        call = session.get(CallSession, call_id)
        if not call:
            return None
        extra = {}
        if call.appointment_id:
            extra["reminders"] = list_appointment_reminders(call.appointment_id)
        return _serialize_call(call, extra)
