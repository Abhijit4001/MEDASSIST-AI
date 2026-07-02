from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    specialty: Mapped[str] = mapped_column(String(80), nullable=False)
    hospital: Mapped[str] = mapped_column(String(120), nullable=False)
    location: Mapped[str] = mapped_column(String(120), nullable=False)
    rating: Mapped[float] = mapped_column(Float, default=4.5)
    email: Mapped[str] = mapped_column(String(120), default="")
    available_slots: Mapped[str] = mapped_column(Text, default="[]")

    appointments: Mapped[list["Appointment"]] = relationship(back_populates="doctor")


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    phone: Mapped[str] = mapped_column(String(20), default="")
    date_of_birth: Mapped[str] = mapped_column(String(20), default="")
    medical_history: Mapped[str] = mapped_column(Text, default="[]")
    allergies: Mapped[str] = mapped_column(Text, default="[]")

    appointments: Mapped[list["Appointment"]] = relationship(back_populates="patient")
    call_sessions: Mapped[list["CallSession"]] = relationship(back_populates="patient")


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), nullable=False)
    datetime: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="scheduled")
    notes: Mapped[str] = mapped_column(Text, default="")
    visit_summary: Mapped[str] = mapped_column(Text, default="")
    booked_via: Mapped[str] = mapped_column(String(40), default="manual")

    patient: Mapped["Patient"] = relationship(back_populates="appointments")
    doctor: Mapped["Doctor"] = relationship(back_populates="appointments")
    reminders: Mapped[list["Reminder"]] = relationship(back_populates="appointment")


class CallSession(Base):
    __tablename__ = "call_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active")
    stage: Mapped[str] = mapped_column(String(40), default="greeting")
    transcript: Mapped[str] = mapped_column(Text, default="[]")
    selected_doctor_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    selected_slot: Mapped[str] = mapped_column(String(30), default="")
    appointment_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    patient: Mapped["Patient"] = relationship(back_populates="call_sessions")


class Reminder(Base):
    __tablename__ = "reminders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    appointment_id: Mapped[int] = mapped_column(ForeignKey("appointments.id"), nullable=False)
    remind_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    channel: Mapped[str] = mapped_column(String(20), default="email")
    message: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="scheduled")
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    job_id: Mapped[str] = mapped_column(String(80), default="")

    appointment: Mapped["Appointment"] = relationship(back_populates="reminders")
