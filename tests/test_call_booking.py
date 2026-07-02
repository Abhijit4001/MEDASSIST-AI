import pytest
from datetime import datetime, timedelta

from app.agents.call_agent import process_call_turn, start_call
from app.database.models import Reminder
from app.database.seed_data import seed_database
from app.services.notification_service import schedule_appointment_reminders


@pytest.fixture(autouse=True)
def setup_db(tmp_path, monkeypatch):
    db_file = tmp_path / "test.db"
    monkeypatch.setattr("app.utils.constants.DB_PATH", db_file)
    monkeypatch.setattr("app.database.db.DB_PATH", db_file)
    monkeypatch.setattr(
        "app.database.db.engine",
        __import__("sqlalchemy").create_engine(
            f"sqlite:///{db_file}", connect_args={"check_same_thread": False}
        ),
    )
    from app.database import db

    db.SessionLocal = db.sessionmaker(bind=db.engine, autoflush=False, autocommit=False)
    seed_database(force=True)
    yield


def test_start_call_returns_greeting():
    result = start_call(1)
    assert result["success"] is True
    assert "MedAssist AI" in result["ai_message"]
    assert result["call"]["stage"] == "collecting_need"


def test_ai_call_books_appointment_and_schedules_reminders():
    started = start_call(1)
    call_id = started["call"]["id"]

    process_call_turn(call_id, "I need a cardiologist in Mumbai")
    process_call_turn(call_id, "Dr. Ananya")
    turn = process_call_turn(call_id, "first")
    confirm = process_call_turn(call_id, "yes")

    assert confirm["booked"] is True
    assert confirm["call"]["status"] == "completed"
    assert confirm["call"]["appointment_id"] is not None
    assert len(confirm["reminders"]) >= 1


def test_schedule_appointment_reminders_uses_future_dates():
    appointment_time = datetime.now() + timedelta(days=3, hours=2)
    reminders = schedule_appointment_reminders(1, appointment_time, "Ananya Sharma")

    assert len(reminders) >= 2
    assert all(datetime.fromisoformat(item["remind_at"]) < appointment_time for item in reminders)

    from app.database.db import get_db

    with get_db() as session:
        rows = session.query(Reminder).filter(Reminder.appointment_id == 1).all()
        assert len(rows) >= 2
