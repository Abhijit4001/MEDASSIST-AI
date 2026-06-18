import os

from dotenv import load_dotenv

load_dotenv()

_api_key = os.getenv("GEMINI_API_KEY", "").strip()
_model = None


def _get_model():
    global _model
    if _model is not None:
        return _model
    if not _api_key:
        return None
    try:
        import google.generativeai as genai

        genai.configure(api_key=_api_key)
        _model = genai.GenerativeModel("gemini-2.0-flash")
        return _model
    except Exception:
        return None


def is_gemini_available() -> bool:
    return _get_model() is not None


def generate_text(prompt: str, system: str = "") -> str:
    model = _get_model()
    if model is None:
        return ""
    full_prompt = f"{system}\n\n{prompt}" if system else prompt
    try:
        response = model.generate_content(full_prompt)
        return response.text.strip()
    except Exception:
        return ""


def classify_intent(message: str) -> str | None:
    from app.utils.constants import (
        INTENT_BOOK,
        INTENT_GENERAL,
        INTENT_RECORDS,
        INTENT_REMINDER,
        INTENT_SEARCH,
        INTENT_SUMMARY,
    )
    from app.utils.prompts import COORDINATOR_SYSTEM

    result = generate_text(message, COORDINATOR_SYSTEM)
    valid = {
        INTENT_SEARCH,
        INTENT_BOOK,
        INTENT_RECORDS,
        INTENT_REMINDER,
        INTENT_SUMMARY,
        INTENT_GENERAL,
    }
    if result in valid:
        return result
    return None
