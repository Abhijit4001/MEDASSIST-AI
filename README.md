# MedAssist AI

MedAssist AI is a multi-agent healthcare assistant for finding doctors, booking appointments through an AI call agent, viewing patient records, and generating visit summaries. It ships with a FastAPI backend, an HTML workspace frontend, SQLite demo data, LangGraph routing, and date-based appointment reminders.

## Features

- Chat endpoint that detects user intent and routes messages to the right agent.
- **AI call booking** that conducts a phone-style conversation, books a slot, and schedules reminders automatically.
- Doctor search by specialty, location, or name.
- Appointment booking, cancellation, and appointment history.
- **Date-based reminders** scheduled for the day before, morning of the visit, and two hours before the appointment.
- Patient profile and medical record lookup.
- Visit summary generation for appointments.
- Optional Gemini integration for richer call and chat responses.
- HTML frontend served directly from FastAPI at `http://127.0.0.1:8000`.

## Tech Stack

- Python 3.11+
- FastAPI and Uvicorn
- LangGraph and LangChain
- SQLAlchemy with SQLite
- ChromaDB for patient interaction memory
- APScheduler for reminder jobs
- Google Gemini SDK (optional)
- Pytest

## Project Structure

```text
app/
  agents/          Healthcare task agents, including AI call booking
  api/             FastAPI routes
  database/        SQLAlchemy models, DB session, seed data
  memory/          ChromaDB and patient memory helpers
  services/        Gemini, email, notifications, reminders
  utils/           Constants, prompts, helpers
  workflows/       LangGraph healthcare workflow
frontend/          HTML/CSS/JS workspace
data/              Exported demo JSON data
tests/             Pytest test suite
```

## Getting Started

### 1. Create a virtual environment

```bash
python -m venv .venv
.venv\Scripts\activate
```

On macOS or Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create or update `.env` in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key
RESEND_API_KEY=your_resend_api_key
FROM_EMAIL=onboarding@resend.dev
```

The app still runs without these keys. It falls back to rule-based call/chat behavior and logs reminder delivery locally when email is not configured.

### 4. Start the app

Run from the project root:

```bash
python -m app
```

Windows alternative if `python` is not on PATH:

```powershell
.\.venv\Scripts\python.exe -m app
```

You can also start Uvicorn directly:

```bash
python -m uvicorn app.main:app --reload
```

Open:

- Frontend workspace: `http://127.0.0.1:8000`
- Swagger docs: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/api/health`

The database is seeded automatically when the API starts.

## AI Call Booking Flow

1. Open the **AI Call** tab in the frontend.
2. Click **Start AI Call**.
3. Allow microphone access when the browser asks.
4. Listen to the AI agent speak, then respond by voice or text.
5. Example voice flow:
   - `I need a cardiologist in Mumbai`
   - `Dr. Ananya`
   - `first`
   - `yes`

Voice features:

- **AI voice**: reads each agent response aloud.
- **Hands-free**: automatically listens after the AI finishes speaking.
- **Hold to speak**: manual push-to-talk using the mic button.

Best supported in Chrome or Edge. If voice is unavailable, type responses in the call input.

When the call completes:

- The appointment is saved in SQLite.
- Reminders are scheduled relative to the appointment date:
  - Day before at 9:00 AM
  - Appointment day at 8:00 AM
  - Two hours before the visit

## API Examples

### Start AI call

```bash
curl -X POST http://127.0.0.1:8000/api/calls/start \
  -H "Content-Type: application/json" \
  -d "{\"patient_id\":1}"
```

### Continue AI call

```bash
curl -X POST http://127.0.0.1:8000/api/calls/1/turn \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"I need a cardiologist in Mumbai\"}"
```

### Chat

```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"Find a cardiologist in Mumbai\",\"patient_id\":1}"
```

### View appointment reminders

```bash
curl http://127.0.0.1:8000/api/appointments/1/reminders
```

## Testing

```bash
pytest
```

## Demo Prompts

Try these in chat:

- `Find a cardiologist in Mumbai`
- `Show my medical records`
- `Set appointment reminder`
- `Summary for appointment #1`

Or use the **AI Call** tab for full booking plus reminder scheduling.

## Notes

- `medassist.db` is the local SQLite database used by the app.
- `data/*.json` files are exported demo records generated from the database.
- `chroma_data/` stores local ChromaDB memory data.
- This project is a demo assistant and should not be used as a substitute for professional medical advice.
