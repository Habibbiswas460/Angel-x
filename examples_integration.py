#!/usr/bin/env python3
"""
Complete Integration Example
Demonstrates all features working together
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

import logging
import pandas as pd
import numpy as np
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


def example_1_broker_integration():
    """Example 1: Connect to broker"""
    print("\n" + "="*60)
    print("EXAMPLE 1: BROKER INTEGRATION")
    print("="*60)
    
    from src.integrations.broker_integration import get_broker
    
    broker = get_broker()
    
    # Try to connect (will fallback if no credentials)
    connected = broker.connect()
    logger.info(f"Broker connection: {connected}")
    
    if connected:
        broker.subscribe_nifty_banknifty()
        logger.info("✓ Subscribed to indices")


def example_2_backtest():
    """Example 2: Run strategy backtest"""
    print("\n" + "="*60)
    print("EXAMPLE 2: STRATEGY BACKTESTING")
    print("="*60)
    
    from src.backtesting import load_backtest_data, run_strategy_backtest
    
    # Load data
    df = load_backtest_data("NIFTY", period='5min')
    logger.info(f"Loaded {len(df)} candles for backtest")
    
    # Define simple strategy
    def simple_ma_strategy(row, trades, capital):
        """Buy on green, sell on red"""
        if row['close'] > row['open'] * 1.002 and not trades:
            return {'action': 'BUY', 'price': row['close'], 'qty': 1}
        elif row['close'] < row['open'] * 0.998 and trades:
            return {'action': 'CLOSE', 'price': row['close']}
        return None
    
    # Run backtest
    result = run_strategy_backtest(df, simple_ma_strategy, "NIFTY", 100000)
    print("\n" + str(result))
    
    return result


def example_3_ml_integration():
    """Example 3: Train and predict with ML"""
    print("\n" + "="*60)
    print("EXAMPLE 3: ML INTEGRATION")
    print("="*60)
    
    from src.backtesting import TickDataLoader
    from src.ml.integration import get_ml_engine
    
    # Load tick data
    loader = TickDataLoader()
    df_ticks = loader.load_latest_ticks()
    
    if df_ticks.empty:
        logger.warning("No tick data available; using synthetic")
        df_ticks = TickDataLoader.create_synthetic_ticks(1000)
    
    # Convert to OHLCV
    df_ohlcv = loader.convert_ticks_to_ohlcv(df_ticks, period='1min')
    logger.info(f"Loaded OHLCV: {len(df_ohlcv)} candles")
    
    # Train ML
    ml = get_ml_engine()
    info = ml.train(df_ohlcv, lookback=50)
    logger.info(f"ML training result: {info}")
    
    # Make predictions
    if not info.get('skipped'):
        predictions = ml.infer(df_ohlcv.iloc[-1])
        logger.info(f"ML predictions: {predictions}")


def example_4_monitoring():
    """Example 4: Setup monitoring"""
    print("\n" + "="*60)
    print("EXAMPLE 4: MONITORING & ALERTS")
    print("="*60)
    
    from src.monitoring import get_monitor, MetricsCollector
    
    monitor = get_monitor()  # No alerts config for this example
    
    # Simulate health check
    metric = monitor.check_health(
        broker_connected=True,
        database_healthy=True,
        api_responding=True,
        memory_usage_mb=MetricsCollector.get_memory_usage(),
        cpu_percent=MetricsCollector.get_cpu_percent(),
        model_trained=True,
        error_count=0
    )
    
    # Get report
    report = monitor.get_status_report()
    logger.info(f"Health status: {report}")


def example_5_multi_leg_strategy():
    """Example 5: Multi-leg strategy (Iron Condor)"""
    print("\n" + "="*60)
    print("EXAMPLE 5: MULTI-LEG STRATEGY")
    print("="*60)
    
    from src.strategies.multi_leg.iron_condor import IronCondor
    
    # Build Iron Condor
    spot = 23000
    ic = IronCondor(underlying="NIFTY", spot=spot, expiry_days=7)
    
    legs = ic.build_legs()
    logger.info(f"Iron Condor legs: {len(legs)}")
    
    for i, leg in enumerate(legs, 1):
        logger.info(f"  Leg {i}: {leg.side} {leg.qty}x {leg.kind}{leg.strike}")


def example_6_prometheus_metrics():
    """Example 6: Prometheus metrics"""
    print("\n" + "="*60)
    print("EXAMPLE 6: PROMETHEUS METRICS")
    print("="*60)
    
    from src.monitoring import get_prometheus_metrics
    
    metrics = get_prometheus_metrics()
    
    # Track some metrics
    metrics.increment('trades_total', 10)
    metrics.increment('trades_winning', 7)
    metrics.set('pnl_total', 50000)
    
    # Export as text
    text_output = metrics.get_text_format()
    logger.info("Prometheus format output:")
    print(text_output)


def main():
    """Run all examples"""
    logger.info("Starting comprehensive integration examples...")
    
    try:
        example_1_broker_integration()
        example_2_backtest()
        example_3_ml_integration()
        example_4_monitoring()
        example_5_multi_leg_strategy()
        example_6_prometheus_metrics()
        
        print("\n" + "="*60)
        print("✓ ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("="*60 + "\n")
        
    except Exception as e:
        logger.error(f"Example error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
