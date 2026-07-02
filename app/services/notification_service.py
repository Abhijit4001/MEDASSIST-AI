from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler

from app.database.db import get_db
from app.database.models import Appointment, Reminder
from app.services.email_service import send_email

_scheduler: BackgroundScheduler | None = None


def get_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler()
        _scheduler.start()
    return _scheduler


def _build_reminder_times(appointment_time: datetime) -> list[tuple[str, datetime, str]]:
    appt_label = appointment_time.strftime("%A, %B %d at %I:%M %p")
    day_before = (appointment_time - timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
    day_of = appointment_time.replace(hour=8, minute=0, second=0, microsecond=0)
    two_hours_before = appointment_time - timedelta(hours=2)

    return [
        (
            "day_before",
            day_before,
            f"Reminder: your appointment is tomorrow ({appt_label}). Please plan your visit.",
        ),
        (
            "day_of",
            day_of,
            f"Reminder: you have an appointment scheduled today ({appt_label}).",
        ),
        (
            "two_hours_before",
            two_hours_before,
            f"Reminder: your appointment starts in about 2 hours ({appt_label}).",
        ),
    ]


def _dispatch_reminder(reminder_id: int) -> None:
    with get_db() as session:
        reminder = session.get(Reminder, reminder_id)
        if not reminder or reminder.status != "scheduled":
            return

        appointment = session.get(Appointment, reminder.appointment_id)
        if not appointment or appointment.status != "scheduled":
            reminder.status = "cancelled"
            return

        patient = appointment.patient
        doctor = appointment.doctor
        body = reminder.message or (
            f"Reminder for your visit with Dr. {doctor.name} "
            f"on {appointment.datetime.strftime('%Y-%m-%d at %H:%M')}."
        )
        result = send_email(patient.email, "MedAssist Appointment Reminder", body)
        reminder.status = "sent" if result.get("sent") else "failed"
        reminder.sent_at = datetime.now()


def _register_job(reminder_id: int, run_at: datetime) -> str:
    scheduler = get_scheduler()
    job_id = f"reminder_{reminder_id}_{int(run_at.timestamp())}"
    scheduler.add_job(
        _dispatch_reminder,
        "date",
        run_date=run_at,
        args=[reminder_id],
        id=job_id,
        replace_existing=True,
    )
    return job_id


def schedule_appointment_reminders(
    appointment_id: int,
    appointment_time: datetime,
    doctor_name: str,
    session=None,
) -> list[dict]:
    if session is not None:
        return _schedule_appointment_reminders(session, appointment_id, appointment_time, doctor_name)

    with get_db() as db_session:
        return _schedule_appointment_reminders(db_session, appointment_id, appointment_time, doctor_name)


def _schedule_appointment_reminders(
    session,
    appointment_id: int,
    appointment_time: datetime,
    doctor_name: str,
) -> list[dict]:
    scheduled: list[dict] = []
    now = datetime.now()

    appointment = session.get(Appointment, appointment_id)
    if not appointment:
        return scheduled

    for reminder_type, remind_at, message in _build_reminder_times(appointment_time):
        if remind_at <= now:
            continue

        reminder = Reminder(
            appointment_id=appointment_id,
            remind_at=remind_at,
            channel="email",
            message=message.replace("your appointment", f"your appointment with Dr. {doctor_name}"),
            status="scheduled",
        )
        session.add(reminder)
        session.flush()
        job_id = _register_job(reminder.id, remind_at)
        reminder.job_id = job_id
        scheduled.append(
            {
                "id": reminder.id,
                "type": reminder_type,
                "remind_at": remind_at.isoformat(),
                "status": reminder.status,
            }
        )

    return scheduled


def bootstrap_reminders() -> None:
    now = datetime.now()
    with get_db() as session:
        pending = (
            session.query(Reminder)
            .filter(Reminder.status == "scheduled", Reminder.remind_at > now)
            .all()
        )
        for reminder in pending:
            if reminder.job_id:
                try:
                    get_scheduler().remove_job(reminder.job_id)
                except Exception:
                    pass
            reminder.job_id = _register_job(reminder.id, reminder.remind_at)


def list_appointment_reminders(appointment_id: int) -> list[dict]:
    with get_db() as session:
        rows = (
            session.query(Reminder)
            .filter(Reminder.appointment_id == appointment_id)
            .order_by(Reminder.remind_at)
            .all()
        )
        return [
            {
                "id": row.id,
                "appointment_id": row.appointment_id,
                "remind_at": row.remind_at.strftime("%Y-%m-%d %H:%M"),
                "channel": row.channel,
                "status": row.status,
                "message": row.message,
                "sent_at": row.sent_at.strftime("%Y-%m-%d %H:%M") if row.sent_at else None,
            }
            for row in rows
        ]


def get_sent_reminders() -> list[dict]:
    with get_db() as session:
        rows = (
            session.query(Reminder)
            .filter(Reminder.status.in_(("sent", "failed")))
            .order_by(Reminder.sent_at.desc())
            .all()
        )
        return [
            {
                "appointment_id": row.appointment_id,
                "remind_at": row.remind_at.isoformat(),
                "sent_at": row.sent_at.isoformat() if row.sent_at else None,
                "status": row.status,
            }
            for row in rows
        ]


# Backward-compatible helper used by older code paths.
def schedule_reminder(
    appointment_id: int,
    patient_email: str,
    doctor_name: str,
    appointment_time: datetime,
    message: str | None = None,
) -> dict:
    del patient_email, message
    scheduled = schedule_appointment_reminders(appointment_id, appointment_time, doctor_name)
    if not scheduled:
        return {"scheduled": False, "sent_immediately": False, "reason": "no_future_reminder_windows"}
    return {"scheduled": True, "reminders": scheduled, "count": len(scheduled)}
