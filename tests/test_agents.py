import pytest

from app.agents.coordinator import detect_intent, route_message
from app.database.seed_data import seed_database
from app.utils.constants import INTENT_BOOK, INTENT_RECORDS, INTENT_SEARCH, INTENT_SUMMARY
from app.workflows.healthcare_graph import run_healthcare_workflow


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


def test_detect_intent_search():
    assert detect_intent("Find a dermatologist in Delhi") == INTENT_SEARCH


def test_detect_intent_book():
    assert detect_intent("Book an appointment with Dr. Ananya") == INTENT_BOOK


def test_detect_intent_records():
    assert detect_intent("Show my medical history") == INTENT_RECORDS


def test_detect_intent_summary():
    assert detect_intent("Generate visit summary for appointment #1") == INTENT_SUMMARY


def test_route_message_returns_response():
    result = route_message("Find a pediatrician in Bangalore")
    assert result["intent"] == INTENT_SEARCH
    assert len(result["response"]) > 0


def test_healthcare_workflow():
    result = run_healthcare_workflow("Show my medical records", patient_id=1)
    assert result["intent"] == INTENT_RECORDS
    assert "arjun" in result["response"].lower() or "patient" in result["response"].lower()
