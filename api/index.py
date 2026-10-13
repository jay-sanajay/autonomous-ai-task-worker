"""
Vercel Serverless Entrypoint for AgentOS FastAPI Backend.
"""

import sys
import os
import traceback

# Add project root to sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

init_error = None
try:
    try:
        from backend.app.database.session import ensure_db_ready
        ensure_db_ready()
    except Exception as dbe:
        print(f"Warning: ensure_db_ready failed: {dbe}")

    from backend.app.main import app as main_app
    app = main_app
except Exception as e:
    init_error = traceback.format_exc()
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse

    app = FastAPI(title="AgentOS Error Fallback")

    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
    async def catch_all_error(path: str):
        return JSONResponse(
            status_code=500,
            content={
                "status": "initialization_error",
                "message": "Backend initialization failed on serverless cold start.",
                "traceback": init_error.splitlines() if init_error else [],
                "sys_path": sys.path,
                "cwd": os.getcwd()
            }
        )

__all__ = ["app"]
