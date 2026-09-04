"""
DB session setup.

Both bots import from here and point at the SAME DATABASE_URL — that
shared connection is what makes user state "live" between the main
bot and the admin bot. No extra sync logic required.

Dev default: SQLite, works out of the box, no server needed.
Production:  set DATABASE_URL to Postgres, e.g.
    postgresql+asyncpg://user:pass@host:5432/cybercalling

SQLite is fine for a handful of trusted users; move to Postgres once
both bots run as separate long-lived processes hitting real concurrency.
"""
import os
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .models import Base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./cybercalling.db")

engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def init_db() -> None:
    """Call once on startup (both bots can call this safely — it's idempotent)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
