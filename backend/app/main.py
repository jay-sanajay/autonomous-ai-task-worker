"""
AgentOS - FastAPI Application Entrypoint.
Hosts REST API for the autonomous agent and the sandbox enterprise application.
"""

from __future__ import annotations
import os
import sys
from contextlib import asynccontextmanager

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.app.database.session import init_db, SessionLocal
from backend.app.database.seed import seed_database
from backend.app.api.tasks import router as tasks_router
from backend.app.api.company import router as company_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize tables and seed sandbox data
    init_db()
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield
    # Shutdown logic if any


app = FastAPI(
    title="AgentOS — Autonomous AI Task Worker",
    description="An AI employee that completes business workflows with independent verification.",
    version="2.0.0",
    lifespan=lifespan
)

# CORS configuration for Vite / React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(tasks_router)
app.include_router(company_router)


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "system": "AgentOS Autonomous Task Worker Gateway",
        "version": "2.0.0"
    }


# Serve compiled frontend assets if available
frontend_dist = os.path.join(PROJECT_ROOT, "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
