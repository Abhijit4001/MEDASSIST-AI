import re
from datetime import datetime
from typing import Any


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def parse_datetime(value: str) -> datetime | None:
    formats = (
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%d-%m-%Y %H:%M",
        "%d-%m-%Y",
        "%Y/%m/%d %H:%M",
    )
    for fmt in formats:
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    return None


def format_doctor_card(doctor: dict[str, Any]) -> str:
    return (
        f"**Dr. {doctor['name']}** — {doctor['specialty']}\n"
        f"  Hospital: {doctor['hospital']} | Location: {doctor['location']}\n"
        f"  Rating: {doctor.get('rating', 'N/A')}/5"
    )


def format_appointment(appointment: dict[str, Any]) -> str:
    return (
        f"Appointment #{appointment['id']}: {appointment['patient_name']} with "
        f"Dr. {appointment['doctor_name']} on {appointment['datetime']} "
        f"[{appointment['status']}]"
    )
