from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from app.database.models import Base
from app.utils.constants import DB_PATH

engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def _ensure_schema() -> None:
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    appointment_columns = {column["name"] for column in inspector.get_columns("appointments")} if inspector.has_table("appointments") else set()
    if "booked_via" not in appointment_columns and inspector.has_table("appointments"):
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE appointments ADD COLUMN booked_via VARCHAR(40) DEFAULT 'manual'"))


def init_db() -> None:
    _ensure_schema()


@contextmanager
def get_db() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_session() -> Session:
    return SessionLocal()
