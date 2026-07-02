from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.agents.call_agent import get_call_session, process_call_turn, start_call
from app.agents.doctor_search_agent import search_doctors
from app.agents.scheduling_agent import book_appointment, cancel_appointment, list_patient_appointments
from app.agents.visit_summary_agent import generate_visit_summary
from app.database.db import get_db
from app.database.models import Doctor, Patient
from app.memory.patient_memory import get_patient_profile
from app.services.notification_service import list_appointment_reminders
from app.workflows.healthcare_graph import run_healthcare_workflow

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    patient_id: int = 1


class ChatResponse(BaseModel):
    intent: str
    response: str
    patient_id: int


class BookRequest(BaseModel):
    patient_id: int
    doctor_id: int
    slot: str
    notes: str = ""


class CallStartRequest(BaseModel):
    patient_id: int = 1


class CallTurnRequest(BaseModel):
    message: str


class DoctorSearchParams(BaseModel):
    specialty: Optional[str] = None
    location: Optional[str] = None
    name: Optional[str] = None


@router.get("/health")
def health_check():
    return {"status": "ok", "service": "MedAssist AI"}


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    result = run_healthcare_workflow(request.message, request.patient_id)
    return ChatResponse(**result)


@router.get("/doctors")
def list_doctors(specialty: str | None = None, location: str | None = None, name: str | None = None):
    return search_doctors(specialty=specialty, location=location, name=name)


@router.get("/doctors/{doctor_id}")
def get_doctor(doctor_id: int):
    with get_db() as session:
        doctor = session.get(Doctor, doctor_id)
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor not found")
        import json
        return {
            "id": doctor.id,
            "name": doctor.name,
            "specialty": doctor.specialty,
            "hospital": doctor.hospital,
            "location": doctor.location,
            "rating": doctor.rating,
            "available_slots": json.loads(doctor.available_slots),
        }


@router.get("/patients/{patient_id}")
def get_patient(patient_id: int):
    profile = get_patient_profile(patient_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Patient not found")
    return profile


@router.get("/patients/{patient_id}/appointments")
def get_appointments(patient_id: int):
    return list_patient_appointments(patient_id)


@router.post("/appointments/book")
def book(request: BookRequest):
    result = book_appointment(request.patient_id, request.doctor_id, request.slot, request.notes)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/appointments/{appointment_id}/cancel")
def cancel(appointment_id: int):
    result = cancel_appointment(appointment_id)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/appointments/{appointment_id}/summary")
def summary(appointment_id: int):
    result = generate_visit_summary(appointment_id)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/calls/start")
def start_ai_call(request: CallStartRequest):
    result = start_call(request.patient_id)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/calls/{call_id}/turn")
def ai_call_turn(call_id: int, request: CallTurnRequest):
    result = process_call_turn(call_id, request.message)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Call failed"))
    return result


@router.get("/calls/{call_id}")
def get_ai_call(call_id: int):
    call = get_call_session(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call session not found")
    return call


@router.get("/appointments/{appointment_id}/reminders")
def appointment_reminders(appointment_id: int):
    return list_appointment_reminders(appointment_id)
