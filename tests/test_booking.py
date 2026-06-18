import pytest

from app.agents.scheduling_agent import book_appointment, cancel_appointment, get_available_slots
from app.database.seed_data import seed_database


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


def test_get_available_slots():
    slots = get_available_slots(1)
    assert isinstance(slots, list)
    assert len(slots) > 0


def test_book_appointment_success():
    slots = get_available_slots(1)
    result = book_appointment(patient_id=1, doctor_id=1, slot=slots[0])
    assert result["success"] is True
    assert "appointment" in result


def test_book_invalid_slot():
    result = book_appointment(patient_id=1, doctor_id=1, slot="2099-01-01 99:99")
    assert result["success"] is False


def test_cancel_appointment():
    slots = get_available_slots(1)
    booked = book_appointment(patient_id=1, doctor_id=1, slot=slots[0])
    appt_id = booked["appointment"]["id"]
    result = cancel_appointment(appt_id)
    assert result["success"] is True
