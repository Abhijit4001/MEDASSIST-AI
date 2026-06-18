import os

from dotenv import load_dotenv

load_dotenv()

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "").strip()
FROM_EMAIL = os.getenv("FROM_EMAIL", "medassist@example.com")


def send_email(to: str, subject: str, body: str) -> dict:
    if not RESEND_API_KEY or not to:
        return {"sent": False, "reason": "email_not_configured"}

    try:
        import resend

        resend.api_key = RESEND_API_KEY
        response = resend.Emails.send(
            {
                "from": FROM_EMAIL,
                "to": [to],
                "subject": subject,
                "html": f"<p>{body}</p>",
            }
        )
        return {"sent": True, "id": response.get("id")}
    except Exception as exc:
        return {"sent": False, "reason": str(exc)}
