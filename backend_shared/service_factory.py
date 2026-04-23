from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend_shared.config import get_settings
from backend_shared.db import ensure_indexes


def create_service_app(*, title: str, description: str):
    settings = get_settings()
    app = FastAPI(title=title, description=description, version="2.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    def startup():
        ensure_indexes()

    @app.get("/health")
    def health():
        return {"service": settings.service_name, "status": "ok"}

    return app
