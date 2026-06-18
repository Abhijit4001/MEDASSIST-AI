# MedAssist AI

MedAssist AI is a multi-agent healthcare assistant for finding doctors, booking appointments, viewing patient records, setting reminders, and generating visit summaries. It includes a FastAPI backend, a Streamlit chat frontend, SQLite-backed demo data, and LangGraph-based routing between healthcare agents.

## Features

- Chat endpoint that detects user intent and routes messages to the right agent.
- Doctor search by specialty, location, or name.
- Appointment booking, cancellation, and appointment history.
- Patient profile and medical record lookup.
- Visit summary generation for appointments.
- Optional Gemini integration for richer intent classification and text generation.
- Streamlit frontend for interactive chat.
- Docker Compose setup for running the API and frontend together.

## Tech Stack

- Python 3.11+
- FastAPI and Uvicorn
- Streamlit
- LangGraph and LangChain
- SQLAlchemy with SQLite
- ChromaDB for patient interaction memory
- Google Gemini SDK
- Pytest

## Project Structure

```text
app/
  agents/          Healthcare task agents
  api/             FastAPI routes
  database/        SQLAlchemy models, DB session, seed data
  memory/          ChromaDB and patient memory helpers
  services/        Gemini, email, and notification services
  utils/           Constants, prompts, helpers
  workflows/       LangGraph healthcare workflow
frontend/          Streamlit and static frontend files
data/              Exported demo JSON data
tests/             Pytest test suite
chroma_data/       Local ChromaDB persistence
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
```

The app can still run without `GEMINI_API_KEY`; it will fall back to rule-based behavior where available.

### 4. Start the API

```bash
uvicorn app.main:app --reload
```

The API will be available at:

- API root: `http://127.0.0.1:8000`
- Swagger docs: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/api/health`

The database is seeded automatically when the API starts.

### 5. Start the Streamlit frontend

In another terminal:

```bash
streamlit run frontend/streamlit_app.py
```

The frontend defaults to `http://127.0.0.1:8000/api` for backend calls.

## Running with Docker

```bash
docker compose up --build
```

Services:

- API: `http://127.0.0.1:8000`
- Frontend: `http://127.0.0.1:8501`

## API Examples

### Chat

```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"Find a cardiologist in Mumbai\",\"patient_id\":1}"
```

### List doctors

```bash
curl "http://127.0.0.1:8000/api/doctors?specialty=Cardiology&location=Mumbai"
```

### Book an appointment

```bash
curl -X POST http://127.0.0.1:8000/api/appointments/book \
  -H "Content-Type: application/json" \
  -d "{\"patient_id\":1,\"doctor_id\":1,\"slot\":\"2026-06-12 10:00\",\"notes\":\"Routine checkup\"}"
```

### View patient appointments

```bash
curl http://127.0.0.1:8000/api/patients/1/appointments
```

## Testing

Run the test suite with:

```bash
pytest
```

The tests create temporary SQLite databases and seed sample data automatically.

## Demo Prompts

Try these in the Streamlit chat:

- `Find a cardiologist in Mumbai`
- `Book Dr. Ananya on 2026-06-12 10:00`
- `Show my medical records`
- `Set appointment reminder`
- `Summary for appointment #1`

## Notes

- `medassist.db` is the local SQLite database used by the app.
- `data/*.json` files are exported demo records generated from the database.
- `chroma_data/` stores local ChromaDB memory data.
- This project is a demo assistant and should not be used as a substitute for professional medical advice.
