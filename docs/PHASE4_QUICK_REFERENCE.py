"""
PHASE 4 — QUICK REFERENCE GUIDE
Copy-paste examples and integration patterns

Smart Money Detector Quick Start
"""

# ============================================================================
# BASIC INITIALIZATION
# ============================================================================

from src.utils.smart_money_engine import SmartMoneyDetector
from src.utils.smart_money_models import SmartMoneyConfig, BattlefieldControl

# Create engine
config = SmartMoneyConfig()  # Uses defaults, or customize:
# config = SmartMoneyConfig(
#     volume_spike_threshold=1.5,
#     trap_low_oi_threshold=50,
#     ce_pe_atm_range=5.0,
# )

engine = SmartMoneyDetector(config=config)
engine.set_universe("NIFTY", atm_strike=20000.0, days_to_expiry=7.0)

# ============================================================================
# FEEDING DATA
# ============================================================================

# From Phase 2B - Option Chain Data
strikes_data = {
    20000: {
        "CE": {
            "ltp": 100,
            "volume": 500,
            "bid": 99,
            "ask": 101,
        },
        "PE": {
            "ltp": 50,
            "volume": 400,
            "bid": 49,
            "ask": 51,
        },
    },
    20100: {
        "CE": {
            "ltp": 80,
            "volume": 450,
            "bid": 79,
            "ask": 81,
        },
        "PE": {
            "ltp": 70,
            "volume": 420,
            "bid": 69,
            "ask": 71,
        },
    },
    # ... more strikes
}

# From Phase 3 - Greeks Engine
greeks_data = {
    20000: {
        "CE": {
            "delta": 0.5,
            "gamma": 0.02,
            "theta": -0.5,
            "vega": 0.1,
            "implied_volatility": 0.25,
            "prev_delta": 0.45,
            "prev_gamma": 0.019,
            "prev_theta": -0.48,
        },
        "PE": {
            "delta": -0.3,
            "gamma": 0.02,
            "theta": -0.4,
            "vega": 0.1,
            "implied_volatility": 0.25,
            "prev_delta": -0.25,
            "prev_gamma": 0.019,
            "prev_theta": -0.38,
        },
    },
    # ... more strikes
}

# OI and Volume data (can be same as Phase 2B or separate)
current_oi_data = {
    20000: {
        "CE": {"oi": 1000, "volume": 500},
        "PE": {"oi": 800, "volume": 400},
    },
    20100: {
        "CE": {"oi": 900, "volume": 450},
        "PE": {"oi": 850, "volume": 420},
    },
    # ... more strikes
}

# Update engine with all data
signal = engine.update_from_market_data(
    strikes_data=strikes_data,
    greeks_data=greeks_data,
    current_oi_data=current_oi_data,
)

# ============================================================================
# USING SIGNALS
# ============================================================================

# Check if can trade
if signal.can_trade:
    print(f"✓ Can trade")
else:
    print(f"✗ Cannot trade: {signal.reason}")

# Get recommendation
recommendation = signal.recommendation
if recommendation == "BUY_CALL":
    print("Direction: Bullish (Buy Call)")
elif recommendation == "BUY_PUT":
    print("Direction: Bearish (Buy Put)")
elif recommendation == "NEUTRAL":
    print("Direction: Neutral (No clear bias)")
else:
    print("Recommendation: AVOID")

# Check for fresh positions (scalping edge)
if signal.fresh_position_detected:
    print(f"🔥 Fresh position detected!")
    print(f"   Strength: {signal.fresh_position_strength:.0%}")
    print(f"   Expected volatility: {signal.fresh_position_strength:.0%}")

# Check market control
if signal.market_control == BattlefieldControl.BULLISH_CONTROL:
    print("Market Control: BULLISH (CE dominance)")
elif signal.market_control == BattlefieldControl.BEARISH_CONTROL:
    print("Market Control: BEARISH (PE dominance)")
elif signal.market_control == BattlefieldControl.BALANCED:
    print("Market Control: BALANCED (50/50)")
else:
    print("Market Control: CHOP (No clear dominance)")

# ============================================================================
# CONVICTION SCORES
# ============================================================================

# OI Conviction (0-1): How certain is OI showing conviction
oi_conviction = signal.oi_conviction_score
if oi_conviction > 0.7:
    print(f"Strong OI conviction: {oi_conviction:.0%}")
elif oi_conviction > 0.5:
    print(f"Moderate OI conviction: {oi_conviction:.0%}")
else:
    print(f"Weak OI conviction: {oi_conviction:.0%}")

# Volume Aggression (0-1): How aggressive is volume
volume_aggression = signal.volume_aggression_score
if volume_aggression > 0.7:
    print(f"Aggressive volume: {volume_aggression:.0%}")
elif volume_aggression > 0.5:
    print(f"Elevated volume: {volume_aggression:.0%}")
else:
    print(f"Normal volume: {volume_aggression:.0%}")

# Smart Money Probability (0-1): Likelihood of smart money move
smart_money_prob = signal.smart_money_probability
print(f"Smart money probability: {smart_money_prob:.0%}")

# Trap Probability (0-1): Risk of fake move
trap_prob = signal.trap_probability
if trap_prob > 0.5:
    print(f"⚠️  HIGH trap risk: {trap_prob:.0%} - AVOID")
elif trap_prob > 0.3:
    print(f"⚠️  Moderate trap risk: {trap_prob:.0%} - CAUTION")
else:
    print(f"✓ Low trap risk: {trap_prob:.0%}")

# ============================================================================
# DETAILED STATUS & METRICS
# ============================================================================

# Get comprehensive diagnostic status
status = engine.get_detailed_status()
print(f"Engine health: {status.health_status}")
print(f"Strikes analyzed: {status.strikes_analyzed}")
print(f"High conviction strikes: {status.high_conviction_strikes}")
print(f"Fresh positions active: {status.fresh_position_count}")
print(f"Signal confidence: {status.signal_confidence:.0%}")

# Get detailed metrics
metrics = engine.get_metrics()
print("\nOI Classifier Metrics:")
print(f"  Long build-ups: {metrics['oi_classifier']['long_buildup']}")
print(f"  Short build-ups: {metrics['oi_classifier']['short_buildup']}")

print("\nVolume Detector Metrics:")
print(f"  Spikes detected: {metrics['volume_detector']['spikes_detected']}")
print(f"  Bursts detected: {metrics['volume_detector']['bursts_detected']}")

print("\nTrap Filter Metrics:")
print(f"  Traps detected: {metrics['trap_filter']['total_traps_detected']}")
print(f"  Trap detection rate: {metrics['trap_filter']['trap_detection_rate']:.1f}%")

# ============================================================================
# COMPONENT-LEVEL ACCESS (Advanced)
# ============================================================================

# Access individual component metrics if needed

# 1. OI Build-Up Classifications
oi_metrics = engine.oi_classifier.get_metrics()
high_conviction_strikes = engine.oi_classifier.get_high_conviction_strikes()
print(f"High conviction: {high_conviction_strikes}")

# 2. Volume Spike Detection
volume_detector_metrics = engine.volume_detector.get_metrics()
print(f"Average volume: {engine.volume_detector.get_average_volume(20000, 'CE')}")

# 3. CE vs PE Battlefield
battlefield = engine.battlefield_analyzer.get_current_battlefield()
if battlefield:
    print(f"CE OI dominance: {battlefield.ce_oi_dominance:.0%}")
    print(f"War intensity: {battlefield.war_intensity:.0%}")
    print(f"CE momentum: {battlefield.ce_momentum:.0%}")

# 4. Fresh Positions
fresh_list = engine.fresh_detector.get_fresh_positions_in_chain(max_age_seconds=300)
for (strike, option_type), info in fresh_list:
    print(f"Fresh: {strike} {option_type}, age={info['age_seconds']}s, decay={info['decay_factor']:.0%}")

# 5. Trap Detection
trap_metrics = engine.trap_filter.get_metrics()
print(f"Scalper traps: {trap_metrics['scalper_traps']}")
print(f"Noise traps: {trap_metrics['noise_traps']}")
print(f"Theta traps: {trap_metrics['theta_traps']}")

# ============================================================================
# SIGNAL SUBSCRIPTION (Real-time Updates)
# ============================================================================

def handle_new_signal(signal):
    """Called whenever a new signal is generated"""
    print(f"\n🎯 NEW SIGNAL: {signal.recommendation}")
    print(f"   OI Conviction: {signal.oi_conviction_score:.0%}")
    print(f"   Can trade: {signal.can_trade}")
    if signal.fresh_position_detected:
        print(f"   🔥 Fresh position detected!")

# Subscribe to signals
engine.subscribe_to_signals(handle_new_signal)

# Later updates will trigger the callback
signal = engine.update_from_market_data(...)  # → Calls handle_new_signal

# Unsubscribe when done
engine.unsubscribe_from_signals(handle_new_signal)

# ============================================================================
# CONTINUOUS MARKET FEED PATTERN
# ============================================================================

class ScalpingBot:
    def __init__(self):
        self.engine = SmartMoneyDetector()
        self.engine.set_universe("NIFTY", 20000.0, 7.0)
        self.last_signal = None
        
        # Subscribe to all signals
        self.engine.subscribe_to_signals(self._on_signal)
    
    def _on_signal(self, signal):
        """Handle new signal from engine"""
        self.last_signal = signal
        
        # Implement your trading logic here
        if signal.can_trade and signal.recommendation == "BUY_CALL":
            self.execute_buy_call()
        elif signal.can_trade and signal.recommendation == "BUY_PUT":
            self.execute_buy_put()
    
    def update_market_feed(self, strikes_data, greeks_data, oi_data):
        """Called with each market update"""
        signal = self.engine.update_from_market_data(
            strikes_data=strikes_data,
            greeks_data=greeks_data,
            current_oi_data=oi_data,
        )
        return signal
    
    def execute_buy_call(self):
        print("Executing: BUY_CALL")
        # TODO: Implement order placement via Angel One API
    
    def execute_buy_put(self):
        print("Executing: BUY_PUT")
        # TODO: Implement order placement via Angel One API

# Usage:
# bot = ScalpingBot()
# for market_update in market_stream:
#     bot.update_market_feed(...)

# ============================================================================
# ERROR HANDLING PATTERN
# ============================================================================

try:
    signal = engine.update_from_market_data(
        strikes_data=strikes_data,
        greeks_data=greeks_data,
        current_oi_data=current_oi_data,
    )
    
    # Check engine health
    status = engine.get_detailed_status()
    if status.health_status != "HEALTHY":
        print(f"⚠️  Engine degraded: {status.health_status}")
        print(f"Issues: {status.warnings}")
    
    # Validate signal
    if not signal.can_trade:
        print(f"Cannot trade: {signal.reason}")
    else:
        # Safe to trade
        print(f"Action: {signal.recommendation}")

except Exception as e:
    print(f"Error processing signal: {e}")
    # Fall back to manual analysis or skip update

# ============================================================================
# INTEGRATION WITH PHASE 3 (GREEKS ENGINE)
# ============================================================================

from src.utils.greeks_engine import GreeksEngine

# Phase 3: Greeks calculation
greeks_engine = GreeksEngine()
greeks_engine.set_universe("NIFTY", 20000.0, 7.0)
greeks_engine.update_from_option_chain(option_chain_dict)

# Extract Greeks for Phase 4
greeks_data = {}
for strike in strikes:
    greeks_data[strike] = {
        "CE": {
            "delta": greeks_engine.get_greeks("CE", strike)["delta"],
            "gamma": greeks_engine.get_greeks("CE", strike)["gamma"],
            # ... etc
        },
        "PE": {
            # ... similar for PE
        },
    }

# Pass to Phase 4
signal = engine.update_from_market_data(
    strikes_data=strikes_data,
    greeks_data=greeks_data,
    current_oi_data=current_oi_data,
)

# ============================================================================
# CONFIGURATION CUSTOMIZATION
# ============================================================================

from src.utils.smart_money_models import SmartMoneyConfig

# Aggressive settings (catch more moves, higher false positives)
config_aggressive = SmartMoneyConfig(
    volume_spike_threshold=1.3,  # Lower threshold
    volume_burst_threshold=2.0,
    fresh_position_oi_jump=0.05,  # 5% instead of 10%
    trap_low_oi_threshold=100,  # Higher threshold
)

# Conservative settings (fewer moves, higher accuracy)
config_conservative = SmartMoneyConfig(
    volume_spike_threshold=2.0,  # Higher threshold
    volume_burst_threshold=3.5,
    fresh_position_oi_jump=0.20,  # 20% requirement
    trap_low_oi_threshold=30,  # Lower threshold
)

engine = SmartMoneyDetector(config=config_aggressive)
# ... use engine

# ============================================================================
# RESET & CLEANUP
# ============================================================================

# Clear all history and metrics
engine.reset()

# Unsubscribe all callbacks
for callback in engine.signal_callbacks.copy():
    engine.unsubscribe_from_signals(callback)

# Start fresh with new universe
engine.set_universe("BANKNIFTY", 45000.0, 3.0)
signal = engine.update_from_market_data(...)

# ============================================================================
# DEBUGGING
# ============================================================================

# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Get full component state
print(engine.oi_classifier.strike_history)  # Raw classification history
print(engine.volume_detector.volume_history)  # Raw volume history

# Check individual strike analysis
key = (20000, "CE")
classification = engine.oi_classifier.get_strike_classification(20000, "CE")
print(f"Classification: {classification}")

# Get health report with issues
status = engine.get_detailed_status()
print(f"Status: {status.health_status}")
print(f"Warnings: {status.warnings}")
print(f"Errors: {status.errors}")

# ============================================================================
# COMMON PATTERNS
# ============================================================================

# Pattern 1: Only trade high conviction setups
if (signal.oi_conviction_score > 0.7 and
    signal.volume_aggression_score > 0.6 and
    signal.trap_probability < 0.3):
    execute_trade(signal.recommendation)

# Pattern 2: Wait for fresh positions
if signal.fresh_position_detected and signal.fresh_position_strength > 0.8:
    execute_trade(signal.recommendation)

# Pattern 3: Follow battlefield control
if signal.market_control == BattlefieldControl.BULLISH_CONTROL:
    if signal.recommendation == "BUY_CALL":
        execute_buy_call()  # High confidence

# Pattern 4: Avoid theta traps
if signal.trap_probability > 0.5:
    skip_this_trade()  # Too risky

# Pattern 5: Scale position size by confidence
position_size = base_size * signal.smart_money_probability
execute_trade(signal.recommendation, size=position_size)
"""
