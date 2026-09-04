"""
================================================================================
  🗄️ CyberCalling 2.0 — SQLAlchemy Database Session Manager
================================================================================
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.app.core.config import settings

# Ensure SQLite connect_args if sqlite is used
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=settings.DEBUG
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def run_auto_migrations():
    """Auto-detect and add missing columns to existing SQLite database tables."""
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            # Check telegram_users columns
            res = conn.execute(text("PRAGMA table_info(telegram_users);")).fetchall()
            existing_cols = [r[1] for r in res] if res else []
            if existing_cols:
                cols_to_add = {
                    "plan_tier": "VARCHAR DEFAULT 'Free'",
                    "language": "VARCHAR DEFAULT 'en'",
                    "hourly_limit": "INTEGER DEFAULT 5",
                    "max_bulk_batch_size": "INTEGER DEFAULT 50",
                    "can_call": "BOOLEAN DEFAULT 1",
                    "can_bulk": "BOOLEAN DEFAULT 1",
                    "can_webcall": "BOOLEAN DEFAULT 1",
                    "can_callback": "BOOLEAN DEFAULT 1",
                    "is_banned": "BOOLEAN DEFAULT 0",
                    "ban_reason": "VARCHAR",
                    "is_suspended": "BOOLEAN DEFAULT 0",
                    "suspended_until": "DATETIME",
                    "calls_this_hour": "INTEGER DEFAULT 0",
                    "admin_notes": "TEXT"
                }
                for col_name, col_type in cols_to_add.items():
                    if col_name not in existing_cols:
                        conn.execute(text(f"ALTER TABLE telegram_users ADD COLUMN {col_name} {col_type};"))
            
            # Check user_call_logs columns
            res_calls = conn.execute(text("PRAGMA table_info(user_call_logs);")).fetchall()
            call_cols = [r[1] for r in res_calls] if res_calls else []
            if call_cols:
                if "quality_rating" not in call_cols:
                    conn.execute(text("ALTER TABLE user_call_logs ADD COLUMN quality_rating INTEGER;"))
            conn.commit()
    except Exception as ex:
        print("Auto-migration notice:", ex)

def get_db():
    """Dependency for obtaining database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Run migrations upon module import
run_auto_migrations()
