"""
AgentOS - Database Engine and Session Management.
"""

from __future__ import annotations
import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from backend.app.database.models import Base

# Database path: use writable /tmp directory if running on Vercel serverless
if os.getenv("VERCEL"):
    DB_PATH = os.getenv("DATABASE_URL", "sqlite:////tmp/agentos.db")
else:
    DB_PATH = os.getenv("DATABASE_URL", "sqlite:///./agentos.db")

engine = create_engine(
    DB_PATH,
    connect_args={"check_same_thread": False} if DB_PATH.startswith("sqlite") else {},
    echo=False
)

# Enable foreign keys for SQLite
if DB_PATH.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Create all tables in database and ensure columns."""
    Base.metadata.create_all(bind=engine)
    if DB_PATH.startswith("sqlite"):
        try:
            with engine.connect() as conn:
                res = conn.exec_driver_sql("PRAGMA table_info(verification_results)")
                existing_cols = [r[1] for r in res.fetchall()]
                if "contract_id" not in existing_cols:
                    conn.exec_driver_sql("ALTER TABLE verification_results ADD COLUMN contract_id INTEGER REFERENCES contracts(id)")
                    conn.commit()

                res_app = conn.exec_driver_sql("PRAGMA table_info(approval_requests)")
                app_cols = [r[1] for r in res_app.fetchall()]
                if "argument_hash" not in app_cols:
                    conn.exec_driver_sql("ALTER TABLE approval_requests ADD COLUMN argument_hash VARCHAR(64)")
                    conn.commit()
        except Exception:
            pass


_is_db_ready = False

def ensure_db_ready():
    """Ensure database schema and baseline seed records exist (critical for serverless)."""
    global _is_db_ready
    if not _is_db_ready:
        init_db()
        try:
            from backend.app.database.seed import seed_database
            db = SessionLocal()
            try:
                seed_database(db)
            finally:
                db.close()
        except Exception:
            pass
        _is_db_ready = True


def get_db():
    """FastAPI Dependency for database session."""
    ensure_db_ready()
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def reset_database():
    from backend.app.database.seed import reset_database as _reset
    _reset()

