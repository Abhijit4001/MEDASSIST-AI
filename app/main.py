from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.database.seed_data import seed_database
from app.services.notification_service import bootstrap_reminders

BASE_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = BASE_DIR / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    seed_database()
    bootstrap_reminders()
    yield


app = FastAPI(
    title="MedAssist AI",
    description="Multi-agent healthcare assistant API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

if FRONTEND_DIR.exists():
    app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="frontend")


@app.get("/")
def root():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "MedAssist AI API", "docs": "/docs"}


@app.get("/style.css", include_in_schema=False)
def frontend_css():
    return FileResponse(FRONTEND_DIR / "style.css")


@app.get("/app.js", include_in_schema=False)
def frontend_js():
    return FileResponse(FRONTEND_DIR / "app.js")
