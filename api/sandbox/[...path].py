"""
Catch-all serverless entrypoint for nested /api/sandbox/* routes on Vercel.
"""

import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from api.index import app

__all__ = ["app"]
