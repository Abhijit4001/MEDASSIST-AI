from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler

from app.services.email_service import send_email

_scheduler: BackgroundScheduler | None = None
_sent_reminders: list[dict] = []


def get_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler()
        _scheduler.start()
    return _scheduler


def schedule_reminder(
    appointment_id: int,
    patient_email: str,
    doctor_name: str,
    appointment_time: datetime,
    message: str | None = None,
) -> dict:
    reminder_text = message or (
        f"Reminder: You have an appointment with Dr. {doctor_name} "
        f"on {appointment_time.strftime('%Y-%m-%d at %H:%M')}."
    )

    def _send():
        result = send_email(
            patient_email,
            "MedAssist Appointment Reminder",
            reminder_text,
        )
        _sent_reminders.append(
            {
                "appointment_id": appointment_id,
                "email": patient_email,
                "sent_at": datetime.now().isoformat(),
                "result": result,
            }
        )

    scheduler = get_scheduler()
    run_at = appointment_time
    if run_at <= datetime.now():
        _send()
        return {"scheduled": False, "sent_immediately": True}

    job_id = f"reminder_{appointment_id}_{int(run_at.timestamp())}"
    scheduler.add_job(_send, "date", run_date=run_at, id=job_id, replace_existing=True)
    return {"scheduled": True, "job_id": job_id, "run_at": run_at.isoformat()}


def get_sent_reminders() -> list[dict]:
    return list(_sent_reminders)
