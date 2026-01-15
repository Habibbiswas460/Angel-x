"""
Database base configuration and session management.

This module provides:
- SQLAlchemy declarative base
- Database engine configuration
- Session management
- Common mixins for all models
- Database initialization utilities
"""

import os
from datetime import datetime
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, Column, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Import configuration
try:
    from config import DB_TYPE, DB_PATH, DATABASE_HOST, DATABASE_PORT, DATABASE_NAME
    from config import DATABASE_USER, DATABASE_PASSWORD, DATABASE_POOL_SIZE
    from config import DATABASE_MAX_OVERFLOW, DATABASE_POOL_RECYCLE, DATABASE_ECHO
except ImportError:
    # Fallback defaults if config not available
    DB_TYPE = os.getenv("DB_TYPE", "sqlite")
    DB_PATH = os.getenv("DB_PATH", "data/angel_x.db")
    DATABASE_HOST = os.getenv("DATABASE_HOST", "localhost")
    DATABASE_PORT = os.getenv("DATABASE_PORT", "5432")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "angel_x")
    DATABASE_USER = os.getenv("DATABASE_USER", "angel_x_user")
    DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD", "")
    DATABASE_POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", "5"))
    DATABASE_MAX_OVERFLOW = int(os.getenv("DATABASE_MAX_OVERFLOW", "10"))
    DATABASE_POOL_RECYCLE = int(os.getenv("DATABASE_POOL_RECYCLE", "3600"))
    DATABASE_ECHO = os.getenv("DATABASE_ECHO", "False").lower() == "true"


# ============================================================================
# DATABASE CONNECTION STRING
# ============================================================================

def get_database_url() -> str:
    """
    Get database connection URL based on configuration.
    
    Returns:
        str: SQLAlchemy database URL
    """
    if DB_TYPE == "postgresql":
        return (
            f"postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}"
            f"@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
        )
    else:  # SQLite
        # Ensure directory exists
        db_dir = os.path.dirname(DB_PATH)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        return f"sqlite:///{DB_PATH}"


# ============================================================================
# ENGINE CONFIGURATION
# ============================================================================

# Get database URL
DATABASE_URL = get_database_url()

# Create engine with appropriate settings
if DB_TYPE == "postgresql":
    engine = create_engine(
        DATABASE_URL,
        pool_size=DATABASE_POOL_SIZE,
        max_overflow=DATABASE_MAX_OVERFLOW,
        pool_recycle=DATABASE_POOL_RECYCLE,
        echo=DATABASE_ECHO,
        pool_pre_ping=True,  # Verify connections before using
    )
else:  # SQLite
    engine = create_engine(
        DATABASE_URL,
        echo=DATABASE_ECHO,
        connect_args={"check_same_thread": False},  # Allow multi-threading
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base
Base = declarative_base()


# ============================================================================
# COMMON MIXINS
# ============================================================================

class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps to models."""
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class PrimaryKeyMixin:
    """Mixin to add auto-incrementing primary key."""
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)


# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

def get_session() -> Session:
    """
    Get a new database session.
    
    Returns:
        Session: SQLAlchemy session
        
    Example:
        >>> session = get_session()
        >>> try:
        >>>     # Do database operations
        >>>     session.commit()
        >>> except Exception:
        >>>     session.rollback()
        >>>     raise
        >>> finally:
        >>>     session.close()
    """
    return SessionLocal()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.
    
    Yields:
        Session: SQLAlchemy session
        
    Example:
        >>> with get_db_session() as session:
        >>>     # Do database operations
        >>>     session.add(trade)
        >>>     # Automatically commits on success, rolls back on error
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

def init_database(drop_existing: bool = False) -> None:
    """
    Initialize database by creating all tables.
    
    Args:
        drop_existing (bool): If True, drop existing tables first
        
    Example:
        >>> init_database()  # Create tables
        >>> init_database(drop_existing=True)  # Recreate all tables
    """
    # Import all models to ensure they're registered with Base
    from src.database.models import Trade, Performance, MarketData, AccountHistory
    
    if drop_existing:
        print("⚠️  Dropping all existing tables...")
        Base.metadata.drop_all(bind=engine)
        print("✅ Dropped all tables")
    
    print("📊 Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully")
    
    # Print table summary
    print(f"\n📋 Tables created:")
    for table_name in Base.metadata.tables.keys():
        print(f"   - {table_name}")
    print()


def check_database_connection() -> bool:
    """
    Check if database connection is working.
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


# ============================================================================
# DATABASE INFO
# ============================================================================

def get_database_info() -> dict:
    """
    Get database configuration information.
    
    Returns:
        dict: Database configuration details
    """
    return {
        "type": DB_TYPE,
        "url": DATABASE_URL.replace(DATABASE_PASSWORD, "***") if DATABASE_PASSWORD else DATABASE_URL,
        "pool_size": DATABASE_POOL_SIZE if DB_TYPE == "postgresql" else "N/A",
        "max_overflow": DATABASE_MAX_OVERFLOW if DB_TYPE == "postgresql" else "N/A",
        "echo": DATABASE_ECHO,
        "tables": list(Base.metadata.tables.keys()) if Base.metadata.tables else []
    }


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "Base",
    "engine",
    "SessionLocal",
    "get_session",
    "get_db_session",
    "init_database",
    "check_database_connection",
    "get_database_info",
    "TimestampMixin",
    "PrimaryKeyMixin",
]
