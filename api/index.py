"""
Vercel Serverless Entrypoint for AgentOS FastAPI Backend.
"""

import sys
import os

# Add project root to sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.database.session import ensure_db_ready
ensure_db_ready()

from backend.app.main import app

# Vercel serverless expects 'app'
__all__ = ["app"]
