import pytest

from app.agents.doctor_search_agent import run_doctor_search, search_doctors
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


def test_search_by_specialty():
    results = search_doctors(specialty="Cardiology")
    assert len(results) >= 1
    assert all("cardio" in r["specialty"].lower() for r in results)


def test_search_by_location():
    results = search_doctors(location="Mumbai")
    assert len(results) >= 1
    assert all(r["location"] == "Mumbai" for r in results)


def test_run_doctor_search_message():
    response = run_doctor_search("Find a cardiologist in Mumbai")
    assert "cardio" in response.lower() or "ananya" in response.lower()
    assert "mumbai" in response.lower()
