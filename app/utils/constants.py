from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
DB_PATH = BASE_DIR / "medassist.db"
CHROMA_DIR = BASE_DIR / "chroma_data"

INTENT_SEARCH = "search_doctor"
INTENT_BOOK = "book_appointment"
INTENT_RECORDS = "patient_records"
INTENT_REMINDER = "reminder"
INTENT_SUMMARY = "visit_summary"
INTENT_GENERAL = "general"

APPOINTMENT_STATUSES = ("scheduled", "completed", "cancelled")
