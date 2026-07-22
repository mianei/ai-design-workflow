"""FastAPI application entrypoint."""
from __future__ import annotations

import sys
from pathlib import Path

# Allow `uvicorn backend.main:app` from repo root
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from backend.config import CORS_ORIGINS, ROOT_DIR
from backend.database.db import init_db
from backend.routers.projects import router as projects_router

STATIC_DIR = ROOT_DIR / "static"

app = FastAPI(
    title="AI Design Workflow Agent",
    description="Product concept workflow for consumer goods teams",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS + ["null", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects_router)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/")
def root():
    index = STATIC_DIR / "index.html"
    if index.exists():
        return RedirectResponse(url="/app")
    return {
        "name": "AI Design Workflow Agent",
        "docs": "/docs",
        "health": "/api/health",
        "html": "/app",
    }


@app.get("/app")
def html_app():
    index = STATIC_DIR / "index.html"
    if not index.exists():
        return {"error": "static/index.html not found"}
    return FileResponse(index)
