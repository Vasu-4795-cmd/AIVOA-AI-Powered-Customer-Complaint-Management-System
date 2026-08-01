import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import Base, engine
from app.routers import copilot, complaints
from app.models import complaint  # noqa: F401 -- ensures model is registered before create_all

logging.basicConfig(level=logging.INFO)
settings = get_settings()

app = FastAPI(
    title="AIVOA Customer Complaint Management API",
    description="AI-powered pharmaceutical customer complaint intake, triage, and QMS logging.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(copilot.router)
app.include_router(complaints.router)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/api/health")
def health():
    return {"status": "ok", "groq_enabled": settings.groq_enabled}
