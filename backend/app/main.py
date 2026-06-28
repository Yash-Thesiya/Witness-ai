"""
FastAPI entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import settings
from app.db.database import engine
from app.routers import auth, upload, commitments

app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(upload.router)
app.include_router(commitments.router)


@app.get("/")
def root():
    return {"app": settings.APP_NAME, "status": "running"}


@app.get("/health")
def health_check():
    db_status = "unknown"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as exc:
        db_status = f"error: {exc}"
    return {
        "status": "ok",
        "database": db_status,
        "environment": settings.ENVIRONMENT,
    }
