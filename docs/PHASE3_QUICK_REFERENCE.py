"""
PHASE 3 — GREEKS ENGINE QUICK REFERENCE
Copy-paste examples and common patterns

Run: python3 docs/PHASE3_GREEKS_ENGINE_COMPLETE.md
"""

# ============================================================================
# 1. BASIC INITIALIZATION
# ============================================================================

from src.utils.greeks_engine import GreeksEngine

engine = GreeksEngine(risk_free_rate=0.06)
engine.set_universe("NIFTY", atm_strike=20000.0, days_to_expiry=7.0)

# ============================================================================
# 2. FEEDING DATA (from Phase 2B Option Chain)
# ============================================================================

# Get from your Phase 2B engine:
from src.utils.option_chain_engine import OptionChainDataEngine

option_chain_engine = OptionChainDataEngine(broker)
option_chain_snapshot = option_chain_engine.get_current_snapshot()

# Convert to Greeks-friendly format:
option_chain_dict = {
    strike: {
        "type": strike_data.option_type.value,  # "CE" or "PE"
        "ltp": strike_data.ltp,
        "oi": strike_data.oi,
        "volume": strike_data.volume,
        "bid": strike_data.bid,
        "ask": strike_data.ask,
    }
    for strike, strike_data in option_chain_snapshot.strikes.items()
}

# Update Greeks engine:
engine.update_from_option_chain(option_chain_dict)

# ============================================================================
# 3. GETTING SIGNALS
# ============================================================================

# Check if data is healthy
if not engine.is_tradeable():
    print("Data unhealthy, skipping trade")
    continue

# Get clean signals (0-1 scale, normalized)
direction_bias = engine.get_direction_bias()      # 0=bearish, 0.5=neutral, 1=bullish
acceleration = engine.get_acceleration_score()    # 0=low, 1=high (Gamma)
theta_pressure = engine.get_theta_pressure()      # 0=safe, 1=danger (Theta decay)
iv_state = engine.get_volatility_state()          # CRUSHING, STABLE_LOW, STABLE_MID, STABLE_HIGH, SURGING

# Get recommendation
recommendation = engine.get_trade_recommendation()  # "BUY_CALL", "BUY_PUT", "AVOID", "NEUTRAL"
confidence = engine.get_confidence()                # 0-1

# ============================================================================
# 4. DECISION LOGIC
# ============================================================================

if engine.is_tradeable():
    # Bullish setup: direction_bias > 0.6, acceleration > 0.5, theta_pressure < 0.3
    if direction_bias > 0.6 and acceleration > 0.5 and theta_pressure < 0.3:
        # Place CALL trade
        place_call_order(strike=engine.atm_strike, quantity=1)
    
    # Bearish setup: direction_bias < 0.4, acceleration > 0.5, theta_pressure < 0.3
    elif direction_bias < 0.4 and acceleration > 0.5 and theta_pressure < 0.3:
        # Place PUT trade
        place_put_order(strike=engine.atm_strike, quantity=1)
    
    # Avoid high theta zones
    elif theta_pressure > 0.7:
        print("High Theta decay zone, skipping trade")
    
    else:
        # Neutral setup, skip
        pass
else:
    print(f"Data issue: {engine.get_detailed_status()}")

# ============================================================================
# 5. MONITORING HEALTH
# ============================================================================

health = engine.get_metrics()
print(f"Signals generated: {health['greeks_signals_generated']}")
print(f"Fake moves blocked: {health['fake_moves_blocked']}")
print(f"Health status: {health['health_summary']['current_status']}")

# Get detailed intelligence
intelligence = engine.get_atm_intelligence()
if intelligence:
    print(f"Gamma peak at: {intelligence.gamma_peak_strike}")
    print(f"Theta kill zone: {intelligence.theta_kill_zone_strike}")
    print(f"Delta battle: {intelligence.delta_battle_direction}")

# ============================================================================
# 6. SUBSCRIPTION (CALLBACKS)
# ============================================================================

def on_signal(signal):
    """Called when new signal generated"""
    print(f"New signal: {signal.trade_recommendation}")
    print(f"  Bias: {signal.direction_bias:.2f}")
    print(f"  Accel: {signal.acceleration_score:.2f}")
    print(f"  Theta: {signal.theta_pressure:.2f}")

engine.subscribe_to_signals(on_signal)

# Later, update will trigger callback:
engine.update_from_option_chain(option_chain_dict)

# ============================================================================
# 7. INTEGRATION LOOP
# ============================================================================

import time
from datetime import datetime

def main_loop():
    """Main trading loop with Greeks intelligence"""
    
    engine = GreeksEngine()
    engine.set_universe("NIFTY", 20000.0, 7.0)
    engine.subscribe_to_signals(on_signal)
    
    while True:
        try:
            # 1. Fetch latest option chain
            option_chain = fetch_option_chain()  # Your Phase 2B source
            
            # 2. Update Greeks
            engine.update_from_option_chain(option_chain)
            
            # 3. Check if tradeable
            if not engine.is_tradeable():
                print(f"[{datetime.now()}] Data unhealthy, waiting...")
                time.sleep(5)
                continue
            
            # 4. Get signals
            bias = engine.get_direction_bias()
            accel = engine.get_acceleration_score()
            theta = engine.get_theta_pressure()
            rec = engine.get_trade_recommendation()
            
            # 5. Execute trades
            if rec == "BUY_CALL" and bias > 0.6 and theta < 0.3:
                place_call_order()
            elif rec == "BUY_PUT" and bias < 0.4 and theta < 0.3:
                place_put_order()
            
            # 6. Log metrics
            metrics = engine.get_metrics()
            print(f"[{datetime.now()}] Greeks: bias={bias:.2f}, accel={accel:.2f}, theta={theta:.2f}, rec={rec}")
            
            time.sleep(5)
        
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main_loop()

# ============================================================================
# 8. COMMON SCENARIOS
# ============================================================================

# SCENARIO 1: Trend Catching (bullish)
if engine.is_tradeable():
    if (engine.get_direction_bias() > 0.65 and 
        engine.get_acceleration_score() > 0.6 and
        engine.get_theta_pressure() < 0.4):
        print("Bullish trend ready - place CALL")

# SCENARIO 2: Volatility Play (Gamma expansion)
if engine.is_tradeable():
    if (engine.get_acceleration_score() > 0.7 and
        engine.get_theta_pressure() < 0.3):
        print("High acceleration zone - scalp with fast exits")

# SCENARIO 3: Theta Trap Avoidance
if engine.is_tradeable():
    if engine.get_theta_pressure() > 0.7:
        print("High Theta decay - AVOID or exit existing trades")

# SCENARIO 4: IV Crush Detection
if engine.get_volatility_state().value == "CRUSHING":
    print("IV falling - expect prices to compress")

# SCENARIO 5: Data Quality Check
status = engine.get_detailed_status()
if status["greeks_count"] < 8:
    print("Insufficient Greeks data")
    
health_summary = status["health_status"]
if not health_summary["can_trade"]:
    print(f"Cannot trade: {health_summary['current_status']}")

# ============================================================================
# 9. REFERENCE: GREEKS INTERPRETATION
# ============================================================================

"""
DELTA (Δ) [Call: 0-1, Put: -1 to 0]
    • Move 1 rupee up → Call ≈ Δ rupee profit
    • ATM Call ~0.5, ATM Put ~-0.5
    • Strategy: Directional bias from ΔΔ (delta change)

GAMMA (Γ) [0-0.2]
    • Delta changes Γ rupee per 1 rupee move
    • High Gamma = high leverage (good for scalping)
    • Low Gamma = stable (safe but less profit potential)
    • Strategy: Look for Gamma expansion (acceleration)

THETA (Θ) [Usually negative]
    • Daily decay = -Θ rupee per day
    • Negative = decay working against position
    • Strategy: Avoid high |Theta| zone, use Theta pressure signal

VEGA (ν) [Positive]
    • 1% IV change → Vega rupee P&L
    • Strategy: Not used in Phase 3 (focus on Delta/Gamma)

CHANGE SIGNALS:
    ΔΔ (Delta Change) → Direction momentum
    Γ Expansion → Acceleration potential
    Θ Spike → Decay acceleration (danger)
    Vega Surge → IV sensitivity shift
"""

# ============================================================================
# 10. DEBUGGING
# ============================================================================

# Get full snapshot
signal = engine.get_current_signal()
print(f"Direction bias: {signal.direction_bias}")
print(f"Acceleration: {signal.acceleration_score}")
print(f"Theta pressure: {signal.theta_pressure}")
print(f"Recommendation: {signal.trade_recommendation}")
print(f"Confidence: {signal.confidence}")
print(f"Fake move detected: {signal.fake_move_detected}")
print(f"Data healthy: {signal.is_data_healthy}")

# Get zone intelligence
intelligence = engine.get_atm_intelligence()
if intelligence:
    print(f"\nZone Intelligence:")
    print(f"  Gamma peak: {intelligence.gamma_peak_strike} (value={intelligence.gamma_peak_value:.4f})")
    print(f"  Theta kill: {intelligence.theta_kill_zone_strike} (value={intelligence.theta_kill_value:.4f})")
    print(f"  ATM Delta battle: {intelligence.delta_battle_direction}")
    print(f"  CE Delta: {intelligence.atm_ce_delta:.3f}, PE Delta: {intelligence.atm_pe_delta:.3f}")

# Get metrics
metrics = engine.get_metrics()
print(f"\nMetrics:")
print(f"  Signals: {metrics['greeks_signals_generated']}")
print(f"  Fake moves blocked: {metrics['fake_moves_blocked']}")
print(f"  Calculator: {metrics['calculator_metrics']}")
print(f"  Health: {metrics['health_summary']}")
