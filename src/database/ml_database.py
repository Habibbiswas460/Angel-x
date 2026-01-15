"""
ANGEL-X Database Layer for ML Data Collection
PostgreSQL schema + async writer for ticks, trades, Greeks history
"""

import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import json

logger = logging.getLogger(__name__)

# Try to import psycopg2 for PostgreSQL
try:
    import psycopg2
    from psycopg2.extras import execute_values

    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    logger.warning("psycopg2 not installed - database features disabled")


class DataCategory(Enum):
    """Data category types for ML training"""

    MARKET_TICK = "market_tick"
    GREEKS_SNAPSHOT = "greeks_snapshot"
    TRADE_ENTRY = "trade_entry"
    TRADE_EXIT = "trade_exit"
    BIAS_UPDATE = "bias_update"
    OI_CHANGE = "oi_change"


@dataclass
class DatabaseConfig:
    """Database connection configuration"""

    host: str = "localhost"
    port: int = 5432
    database: str = "angelx_ml"
    user: str = "angelx"
    password: str = ""

    # Performance tuning
    connection_pool_size: int = 5
    batch_size: int = 100  # Batch inserts for performance
    async_mode: bool = True


class MLDatabaseSchema:
    """
    SQL schema for ML data collection

    Tables:
    - market_ticks: Real-time price/volume data
    - greeks_snapshots: Greeks evolution over time
    - trades: Complete trade lifecycle
    - bias_history: Market bias changes
    - oi_changes: Open interest tracking
    """

    CREATE_TABLES_SQL = """
    -- Market ticks (LTP, volume, bid/ask)
    CREATE TABLE IF NOT EXISTS market_ticks (
        id SERIAL PRIMARY KEY,
        timestamp TIMESTAMPTZ NOT NULL,
        symbol VARCHAR(50) NOT NULL,
        ltp DECIMAL(10,2) NOT NULL,
        bid DECIMAL(10,2),
        ask DECIMAL(10,2),
        volume BIGINT,
        oi BIGINT
    );
    CREATE INDEX IF NOT EXISTS idx_ticks_timestamp ON market_ticks (timestamp);
    CREATE INDEX IF NOT EXISTS idx_ticks_symbol ON market_ticks (symbol);
    
    -- Greeks snapshots
    CREATE TABLE IF NOT EXISTS greeks_snapshots (
        id SERIAL PRIMARY KEY,
        timestamp TIMESTAMPTZ NOT NULL,
        symbol VARCHAR(50) NOT NULL,
        underlying VARCHAR(20) NOT NULL,
        strike INTEGER NOT NULL,
        option_type VARCHAR(2) NOT NULL,
        expiry_date DATE NOT NULL,
        ltp DECIMAL(10,2),
        delta DECIMAL(8,4),
        gamma DECIMAL(8,6),
        theta DECIMAL(8,4),
        vega DECIMAL(8,4),
        iv DECIMAL(8,4),
        oi BIGINT,
        volume BIGINT
    );
    CREATE INDEX IF NOT EXISTS idx_greeks_timestamp ON greeks_snapshots (timestamp);
    CREATE INDEX IF NOT EXISTS idx_greeks_symbol ON greeks_snapshots (symbol);
    CREATE INDEX IF NOT EXISTS idx_greeks_strike ON greeks_snapshots (strike, option_type);
    
    -- Trades (complete lifecycle)
    CREATE TABLE IF NOT EXISTS trades (
        id SERIAL PRIMARY KEY,
        trade_id VARCHAR(100) UNIQUE NOT NULL,
        entry_time TIMESTAMPTZ NOT NULL,
        exit_time TIMESTAMPTZ,
        underlying VARCHAR(20) NOT NULL,
        strike INTEGER NOT NULL,
        option_type VARCHAR(2) NOT NULL,
        expiry_date DATE,
        
        -- Entry
        entry_price DECIMAL(10,2) NOT NULL,
        entry_delta DECIMAL(8,4),
        entry_gamma DECIMAL(8,6),
        entry_theta DECIMAL(8,4),
        entry_iv DECIMAL(8,4),
        entry_oi BIGINT,
        entry_reason VARCHAR(200),
        entry_bias VARCHAR(20),
        entry_bias_confidence DECIMAL(5,2),
        
        -- Exit
        exit_price DECIMAL(10,2),
        exit_delta DECIMAL(8,4),
        exit_gamma DECIMAL(8,6),
        exit_theta DECIMAL(8,4),
        exit_iv DECIMAL(8,4),
        exit_reason VARCHAR(200),
        
        -- Performance
        quantity INTEGER NOT NULL,
        pnl DECIMAL(10,2),
        pnl_percent DECIMAL(8,4),
        holding_seconds INTEGER,
        
        -- Risk management
        sl_price DECIMAL(10,2),
        target_price DECIMAL(10,2),
        max_favorable_move DECIMAL(8,4),
        max_adverse_move DECIMAL(8,4)
    );
    CREATE INDEX IF NOT EXISTS idx_trades_entry_time ON trades (entry_time);
    CREATE INDEX IF NOT EXISTS idx_trades_underlying ON trades (underlying);
    CREATE INDEX IF NOT EXISTS idx_trades_pnl ON trades (pnl);
    
    -- Bias history
    CREATE TABLE IF NOT EXISTS bias_history (
        id SERIAL PRIMARY KEY,
        timestamp TIMESTAMPTZ NOT NULL,
        bias VARCHAR(20) NOT NULL,
        confidence DECIMAL(5,2) NOT NULL,
        underlying_ltp DECIMAL(10,2)
    );
    CREATE INDEX IF NOT EXISTS idx_bias_timestamp ON bias_history (timestamp);
    
    -- OI changes (for smart money tracking)
    CREATE TABLE IF NOT EXISTS oi_changes (
        id SERIAL PRIMARY KEY,
        timestamp TIMESTAMPTZ NOT NULL,
        symbol VARCHAR(50) NOT NULL,
        strike INTEGER NOT NULL,
        option_type VARCHAR(2) NOT NULL,
        oi_current BIGINT NOT NULL,
        oi_change BIGINT NOT NULL,
        price_change DECIMAL(8,4),
        volume BIGINT
    );
    CREATE INDEX IF NOT EXISTS idx_oi_timestamp ON oi_changes (timestamp);
    CREATE INDEX IF NOT EXISTS idx_oi_strike ON oi_changes (strike, option_type);
    
    -- ML features (derived/aggregated for training)
    CREATE TABLE IF NOT EXISTS ml_features (
        id SERIAL PRIMARY KEY,
        timestamp TIMESTAMPTZ NOT NULL,
        feature_set JSONB NOT NULL,
        label VARCHAR(50)
    );
    CREATE INDEX IF NOT EXISTS idx_features_timestamp ON ml_features (timestamp);
    CREATE INDEX IF NOT EXISTS idx_features_label ON ml_features (label);
    """


class MLDatabase:
    """
    ML Database interface for ANGEL-X

    Features:
    - Async batch writing for performance
    - Automatic schema creation
    - Query helpers for ML data extraction
    """

    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig()
        self.conn = None
        self.batch_buffer = {cat: [] for cat in DataCategory}

        if not POSTGRES_AVAILABLE:
            logger.warning("PostgreSQL not available - running in no-op mode")
            self.enabled = False
            return

        self.enabled = True
        logger.info(f"MLDatabase initialized (host={self.config.host})")

    def connect(self) -> bool:
        """Connect to PostgreSQL database"""
        if not self.enabled:
            return False

        try:
            self.conn = psycopg2.connect(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.user,
                password=self.config.password,
            )
            logger.info("✓ Connected to ML database")
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            self.enabled = False
            return False

    def create_schema(self):
        """Create database schema"""
        if not self.enabled or not self.conn:
            return

        try:
            cursor = self.conn.cursor()
            cursor.execute(MLDatabaseSchema.CREATE_TABLES_SQL)
            self.conn.commit()
            logger.info("✓ Database schema created/verified")
        except Exception as e:
            logger.error(f"Schema creation failed: {e}")

    def insert_market_tick(
        self,
        timestamp: datetime,
        symbol: str,
        ltp: float,
        bid: Optional[float] = None,
        ask: Optional[float] = None,
        volume: Optional[int] = None,
        oi: Optional[int] = None,
    ):
        """Insert market tick data"""
        if not self.enabled:
            return

        data = {
            "timestamp": timestamp,
            "symbol": symbol,
            "ltp": ltp,
            "bid": bid,
            "ask": ask,
            "volume": volume,
            "oi": oi,
        }

        self.batch_buffer[DataCategory.MARKET_TICK].append(data)

        # Flush if batch full
        if len(self.batch_buffer[DataCategory.MARKET_TICK]) >= self.config.batch_size:
            self._flush_batch(DataCategory.MARKET_TICK)

    def insert_greeks_snapshot(
        self,
        timestamp: datetime,
        symbol: str,
        underlying: str,
        strike: int,
        option_type: str,
        expiry_date: str,
        ltp: float,
        delta: float,
        gamma: float,
        theta: float,
        vega: float,
        iv: float,
        oi: int,
        volume: int,
    ):
        """Insert Greeks snapshot"""
        if not self.enabled:
            return

        data = {
            "timestamp": timestamp,
            "symbol": symbol,
            "underlying": underlying,
            "strike": strike,
            "option_type": option_type,
            "expiry_date": expiry_date,
            "ltp": ltp,
            "delta": delta,
            "gamma": gamma,
            "theta": theta,
            "vega": vega,
            "iv": iv,
            "oi": oi,
            "volume": volume,
        }

        self.batch_buffer[DataCategory.GREEKS_SNAPSHOT].append(data)

        if len(self.batch_buffer[DataCategory.GREEKS_SNAPSHOT]) >= self.config.batch_size:
            self._flush_batch(DataCategory.GREEKS_SNAPSHOT)

    def insert_trade(self, trade_data: Dict[str, Any]):
        """Insert complete trade record"""
        if not self.enabled or not self.conn:
            return

        try:
            cursor = self.conn.cursor()
            query = """
                INSERT INTO trades (
                    trade_id, entry_time, exit_time, underlying, strike, option_type,
                    expiry_date, entry_price, entry_delta, entry_gamma, entry_theta,
                    entry_iv, entry_oi, entry_reason, entry_bias, entry_bias_confidence,
                    exit_price, exit_delta, exit_gamma, exit_theta, exit_iv, exit_reason,
                    quantity, pnl, pnl_percent, holding_seconds, sl_price, target_price
                ) VALUES (
                    %(trade_id)s, %(entry_time)s, %(exit_time)s, %(underlying)s, %(strike)s, 
                    %(option_type)s, %(expiry_date)s, %(entry_price)s, %(entry_delta)s, 
                    %(entry_gamma)s, %(entry_theta)s, %(entry_iv)s, %(entry_oi)s, 
                    %(entry_reason)s, %(entry_bias)s, %(entry_bias_confidence)s,
                    %(exit_price)s, %(exit_delta)s, %(exit_gamma)s, %(exit_theta)s, 
                    %(exit_iv)s, %(exit_reason)s, %(quantity)s, %(pnl)s, %(pnl_percent)s, 
                    %(holding_seconds)s, %(sl_price)s, %(target_price)s
                )
            """
            cursor.execute(query, trade_data)
            self.conn.commit()
            logger.debug(f"Trade {trade_data['trade_id']} saved to database")
        except Exception as e:
            logger.error(f"Trade insert failed: {e}")

    def _flush_batch(self, category: DataCategory):
        """Flush batched inserts"""
        if not self.enabled or not self.conn:
            return

        batch = self.batch_buffer[category]
        if not batch:
            return

        try:
            cursor = self.conn.cursor()

            if category == DataCategory.MARKET_TICK:
                query = """
                    INSERT INTO market_ticks (timestamp, symbol, ltp, bid, ask, volume, oi)
                    VALUES %s
                """
                values = [
                    (d["timestamp"], d["symbol"], d["ltp"], d["bid"], d["ask"], d["volume"], d["oi"]) for d in batch
                ]
                execute_values(cursor, query, values)

            elif category == DataCategory.GREEKS_SNAPSHOT:
                query = """
                    INSERT INTO greeks_snapshots 
                    (timestamp, symbol, underlying, strike, option_type, expiry_date,
                     ltp, delta, gamma, theta, vega, iv, oi, volume)
                    VALUES %s
                """
                values = [
                    (
                        d["timestamp"],
                        d["symbol"],
                        d["underlying"],
                        d["strike"],
                        d["option_type"],
                        d["expiry_date"],
                        d["ltp"],
                        d["delta"],
                        d["gamma"],
                        d["theta"],
                        d["vega"],
                        d["iv"],
                        d["oi"],
                        d["volume"],
                    )
                    for d in batch
                ]
                execute_values(cursor, query, values)

            self.conn.commit()
            logger.debug(f"Flushed {len(batch)} {category.value} records")

            # Clear batch
            self.batch_buffer[category] = []

        except Exception as e:
            logger.error(f"Batch flush failed for {category.value}: {e}")

    def flush_all(self):
        """Flush all pending batches"""
        for category in DataCategory:
            self._flush_batch(category)

    def query_ml_dataset(self, start_date: datetime, end_date: datetime, underlying: str = "NIFTY") -> List[Dict]:
        """
        Query complete ML dataset for training

        Returns:
            List of dicts with features + labels
        """
        if not self.enabled or not self.conn:
            return []

        try:
            cursor = self.conn.cursor()
            query = """
                SELECT 
                    t.*,
                    gs_entry.delta as entry_delta,
                    gs_entry.gamma as entry_gamma,
                    gs_entry.iv as entry_iv,
                    gs_exit.delta as exit_delta,
                    gs_exit.gamma as exit_gamma,
                    gs_exit.iv as exit_iv
                FROM trades t
                LEFT JOIN greeks_snapshots gs_entry ON 
                    t.underlying = gs_entry.underlying AND
                    t.strike = gs_entry.strike AND
                    t.option_type = gs_entry.option_type AND
                    gs_entry.timestamp <= t.entry_time
                LEFT JOIN greeks_snapshots gs_exit ON
                    t.underlying = gs_exit.underlying AND
                    t.strike = gs_exit.strike AND
                    t.option_type = gs_exit.option_type AND
                    gs_exit.timestamp <= t.exit_time
                WHERE t.entry_time BETWEEN %s AND %s
                    AND t.underlying = %s
                ORDER BY t.entry_time
            """
            cursor.execute(query, (start_date, end_date, underlying))

            columns = [desc[0] for desc in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]

            logger.info(f"Fetched {len(results)} ML training records")
            return results

        except Exception as e:
            logger.error(f"ML dataset query failed: {e}")
            return []

    def close(self):
        """Close database connection"""
        if self.conn:
            self.flush_all()
            self.conn.close()
            logger.info("Database connection closed")


# Global database instance
_ml_database = None


def get_ml_database(config: Optional[DatabaseConfig] = None) -> MLDatabase:
    """Get or create global ML database instance"""
    global _ml_database
    if _ml_database is None:
        _ml_database = MLDatabase(config)
        if _ml_database.enabled:
            _ml_database.connect()
            _ml_database.create_schema()
    return _ml_database
