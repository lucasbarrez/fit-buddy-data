"""Asynchronous database manager for backend operations.

Handles all database operations using SQLAlchemy async engine with PostgreSQL.
Manages initialization, CRUD operations for documents, chapters, and deep courses.

Some functions are created but not yet used in the codebase.
"""

from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from src.config import database_settings
from src.bdd.query import *
from src.bdd.schema import Base

# Database URL configuration
DATABASE_URL_SYNC = database_settings.dsn

# Convert sync DSN to async DSN
if "+asyncpg" not in DATABASE_URL_SYNC:
    if "+psycopg2" in DATABASE_URL_SYNC:
        DATABASE_URL_ASYNC = DATABASE_URL_SYNC.replace("+psycopg2", "+asyncpg")
    else:
        DATABASE_URL_ASYNC = DATABASE_URL_SYNC.replace(
            "postgresql://", "postgresql+asyncpg://"
        )
else:
    DATABASE_URL_ASYNC = DATABASE_URL_SYNC

print("🧩 Async DSN:", DATABASE_URL_ASYNC)


class DBManager:
    """
    Asynchronous database manager.

    """

    def __init__(self):
        """Initialize async engine and session factory."""
        # Async engine for all backend operations
        self.engine = create_async_engine(DATABASE_URL_ASYNC, echo=False, future=True)
        self.SessionLocal = async_sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )
        print("⚙️  Async engine initialized (backend).")


    async def create_db(self):
        """
        Initialize complete database.

        """
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Database tables created.")

    async def get_db(self):
        """Context manager for async database session."""
        async with self.SessionLocal() as session:
            yield session

    async def clear_tables(self):
        """Clear all tables without dropping them."""
        async with self.engine.begin() as conn:
            await conn.execute(CLEAR_ALL_TABLES)
        print("🧹 Tables cleared.")

    async def clear_db(self):
        """Drop all tables (ADK + business logic)."""
        async with self.engine.begin() as conn:
            await conn.execute(DROP_ALL_TABLES)
        print("💣 All tables dropped.")

    async def test_db(self):
        """Test database connection and list existing tables."""
        async with self.engine.begin() as conn:
            result = await conn.execute(CHECK_TABLES)
            tables = [row[0] for row in result.fetchall()]
        print("📋 Existing tables:", tables)
        return tables
    
    async def populate_initial_data(self):
        """Populate initial data into the database."""
        async with self.engine.begin() as conn:
            await conn.execute(ENABLE_PGCRYPTO)
            await conn.execute(POPULATE_TABLES)
        print("🌱 Initial data populated.")

