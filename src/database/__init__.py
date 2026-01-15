"""
ANGEL-X Database Module

This module provides:
- ML data collection and storage layer
- Trading database (trades, performance, market data, account history)
- SQLAlchemy models and session management
"""

# ML Database
try:
    from src.database.ml_database import MLDatabase, DatabaseConfig, DataCategory, MLDatabaseSchema, get_ml_database
    HAS_ML_DB = True
except ImportError:
    HAS_ML_DB = False

# Trading Database
try:
    from src.database.base import Base, get_session, get_db_session, init_database, SessionLocal, engine
    from src.database.base import check_database_connection, get_database_info
    HAS_TRADING_DB = True
except ImportError:
    HAS_TRADING_DB = False

__all__ = []

if HAS_ML_DB:
    __all__.extend(["MLDatabase", "DatabaseConfig", "DataCategory", "MLDatabaseSchema", "get_ml_database"])

if HAS_TRADING_DB:
    __all__.extend(["Base", "get_session", "get_db_session", "init_database", "SessionLocal", "engine", 
                    "check_database_connection", "get_database_info"])
