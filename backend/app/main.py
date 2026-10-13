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

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.app.database.session import init_db, SessionLocal
from backend.app.database.seed import seed_database
from backend.app.api.tasks import router as tasks_router
from backend.app.api.company import router as company_router
from backend.app.portal.router import portal_router
from backend.app.api.advanced import advanced_router


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

@app.middleware("http")
async def normalize_api_path(request, call_next):
    # Recover original requested path if forwarded by serverless rewrite
    forwarded_uri = (
        request.headers.get("x-forwarded-uri")
        or request.headers.get("x-matched-path")
        or request.headers.get("x-now-route-matches")
    )
    if forwarded_uri:
        clean_path = forwarded_uri.split("?")[0]
        if clean_path.startswith("/api") or clean_path.startswith("/portal"):
            request.scope["path"] = clean_path

    # Ensure serverless environments that strip the /api prefix still route correctly
    path = request.scope.get("path", "")
    if path and not path.startswith("/api") and not path.startswith("/portal") and not path.startswith("/assets") and path != "/":
        request.scope["path"] = f"/api{path}"
    response = await call_next(request)
    return response

# Include Routers
app.include_router(tasks_router)
app.include_router(company_router)
app.include_router(portal_router)
app.include_router(portal_router, prefix="/api")
app.include_router(advanced_router)


@app.get("/health")
@app.get("/api/health")
@app.get("/api")
@app.get("/api/index")
def health_check():
    return {
        "status": "healthy",
        "system": "AgentOS Autonomous Task Worker Gateway",
        "version": "2.0.0"
    }



# Serve compiled frontend assets if available
possible_dist_dirs = [
    os.path.join(PROJECT_ROOT, "dist"),
    os.path.join(PROJECT_ROOT, "frontend", "dist"),
    os.path.abspath(os.path.join(os.getcwd(), "dist")),
    os.path.abspath(os.path.join(os.getcwd(), "frontend", "dist")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "dist")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")),
]
frontend_dist = next((d for d in possible_dist_dirs if os.path.exists(d)), None)

if frontend_dist:
    assets_dir = os.path.join(frontend_dist, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/") or full_path.startswith("portal/"):
            return FileResponse(os.path.join(frontend_dist, "index.html"), status_code=404)
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
