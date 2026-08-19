"""
Database configuration module.

Sets up the asynchronous SQLAlchemy 2.0 engine, async session maker,
and declarative base class, as well as the FastAPI database session dependency.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

# Import application settings containing the DATABASE_URL
from app.config import settings

# 1. Create the SQLAlchemy Async Engine.
# - future=True: Enables SQLAlchemy 2.0 style behavior.
# - pool_pre_ping=True: Liveness check to handle database restarts or connection drops gracefully.
engine = create_async_engine(
    settings.DATABASE_URL,
    future=True,
    pool_pre_ping=True,
)

# 2. Create the AsyncSession factory.
# - bind=engine: Configures the session maker to use our async engine.
# - autoflush=False: Disables automatic flushing of changes to the DB before queries.
# - expire_on_commit=False: Prevents attributes from expiring after a commit,
#   which is essential in async applications to avoid implicit lazy-loading exceptions.
SessionLocal = async_sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


# 3. Create the Declarative Base class.
# In SQLAlchemy 2.0, models inherit from a class subclassing DeclarativeBase.
class Base(DeclarativeBase):
    """
    Declarative Base class for SQLAlchemy 2.0 models.
    All system models must inherit from this class to be registered.
    """
    pass


# 4. Create an async dependency function get_db() for FastAPI.
# This yields an AsyncSession instance and guarantees cleanup at the end of the request.
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields an asynchronous database session.
    
    The session is managed within an async context manager to ensure it is
    automatically closed after the request is completed, even in the event
    of an unhandled exception.
    """
    async with SessionLocal() as session:
        yield session
