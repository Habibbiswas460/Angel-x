"""
PHASE 3 — Greeks Engine Orchestrator (Main)
Coordinates all Greeks components into clean signals for strategy

Components:
    • GreeksEngine - Main orchestrator
    • Integration with Phase 2B OptionChainDataEngine
    • Clean interface for strategy layer
"""

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Callable, List

from .greeks_models import (
    GreeksSnapshot, OptionType, StrategySignal, 
    GreeksHealthStatus, VolatilityState, AtmIntelligence
)
from .greeks_calculator import GreeksCalculationEngine
from .greeks_change_engine import GreeksChangeTracker, ZoneDetector, MomentumAnalyzer
from .greeks_oi_sync import GreeksOiSyncValidator
from .greeks_health import GreeksHealthMonitor
from .option_chain_data_models import StrikeData

logger = logging.getLogger(__name__)


class GreeksEngine:
    """
    Main Greeks orchestrator
    
    Pipeline:
        Phase 2B Option Chain → Calculate Greeks → Track Changes →
        Validate OI Sync → Health Check → Strategy Signal
    
    Exposes clean interface: get_direction_bias(), get_acceleration(), get_theta_pressure()
    """
    
    def __init__(self, risk_free_rate: float = 0.06):
        """Initialize Greeks engine"""
        # Component initialization
        self.calculator = GreeksCalculationEngine(risk_free_rate=risk_free_rate)
        self.change_tracker = GreeksChangeTracker()
        self.zone_detector = ZoneDetector()
        self.momentum_analyzer = MomentumAnalyzer()
        self.oi_sync_validator = GreeksOiSyncValidator()
        self.health_monitor = GreeksHealthMonitor()
        
        # State tracking
        self.current_greeks: Dict[float, GreeksSnapshot] = {}  # strike -> Greeks
        self.previous_greeks: Dict[float, GreeksSnapshot] = {}  # For delta tracking
        self.current_oi_data: Dict[float, StrikeData] = {}     # strike -> OI data
        self.previous_oi_data: Dict[float, StrikeData] = {}    # For sync validation
        
        self.atm_intelligence: Optional[AtmIntelligence] = None
        self.current_signal: Optional[StrategySignal] = None
        
        # Universe definition
        self.underlying: Optional[str] = None
        self.atm_strike: Optional[float] = None
        self.days_to_expiry: float = 0.0
        
        # Threading
        self.background_update_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.update_interval = 5.0  # seconds
        
        # Callbacks
        self.signal_callbacks: List[Callable[[StrategySignal], None]] = []
        
        # Metrics
        self.signal_count = 0
        self.fake_moves_blocked = 0
        self.theta_exits_triggered = 0
        
        logger.info("Greeks Engine initialized")
    
    def set_universe(
        self,
        underlying: str,
        atm_strike: float,
        days_to_expiry: float
    ):
        """Set trading universe (ATM reference, time to expiry)"""
        self.underlying = underlying
        self.atm_strike = atm_strike
        self.days_to_expiry = days_to_expiry
        logger.info(
            f"Greeks universe set: {underlying} ATM={atm_strike}, "
            f"expiry in {days_to_expiry:.1f} days"
        )
    
    def update_from_option_chain(
        self,
        option_chain_snapshot: Dict,
        broker_greeks: Optional[Dict] = None,
        broker_iv: Optional[Dict] = None
    ):
        """
        Update Greeks from Phase 2B Option Chain snapshot
        
        Input format:
            option_chain_snapshot: {
                strike: {"type": "CE"/"PE", "ltp": X, "oi": Y, ...}
            }
            broker_greeks: {
                strike: {"delta": d, "gamma": g, "theta": t, "vega": v}
            }
            broker_iv: {
                strike: iv_value
            }
        """
        if not self.atm_strike or not self.underlying:
            logger.warning("Universe not set, skipping Greeks update")
            return
        
        # Shift: current → previous
        self.previous_greeks = dict(self.current_greeks)
        self.previous_oi_data = dict(self.current_oi_data)
        
        # Clear current
        self.current_greeks = {}
        self.current_oi_data = {}
        
        # -------- Calculate Greeks for each strike --------
        for strike, chain_data in option_chain_snapshot.items():
            try:
                # Determine option type
                option_type = OptionType.CALL if chain_data.get("type") == "CE" else OptionType.PUT
                
                # Get broker data if available
                broker_greek = broker_greeks.get(strike) if broker_greeks else None
                broker_iv_val = broker_iv.get(strike) if broker_iv else None
                
                # Calculate Greeks
                greek_snapshot, status = self.calculator.calculate_greeks(
                    strike=strike,
                    option_type=option_type,
                    spot=self.atm_strike,
                    days_to_expiry=self.days_to_expiry,
                    ltp=chain_data.get("ltp", 0.0),
                    broker_greeks=broker_greek,
                    broker_iv=broker_iv_val
                )
                
                # Store Greek
                self.current_greeks[strike] = greek_snapshot
                
                # Store OI data for sync validation
                oi_data = StrikeData(
                    strike=strike,
                    option_type=option_type,
                    ltp=chain_data.get("ltp", 0.0),
                    bid=chain_data.get("bid", 0.0),
                    ask=chain_data.get("ask", 0.0),
                    open_interest=chain_data.get("oi", 0),
                    volume=chain_data.get("volume", 0),
                    timestamp=datetime.now()
                )
                self.current_oi_data[strike] = oi_data
                
            except Exception as e:
                logger.error(f"Error updating Greeks for strike {strike}: {e}")
                continue
        
        # -------- Post-update analysis --------
        self._analyze_greeks()
        self._generate_strategy_signal()
    
    def _analyze_greeks(self):
        """Analyze Greeks and generate intelligence"""
        if not self.current_greeks:
            return
        
        # Zone analysis
        self.atm_intelligence = self.zone_detector.analyze_atm_zone(
            self.atm_strike,
            self.current_greeks
        )
        
        logger.debug(
            f"ATM Intelligence: Gamma peak at {self.atm_intelligence.gamma_peak_strike}, "
            f"Theta kill at {self.atm_intelligence.theta_kill_zone_strike}, "
            f"Delta battle: {self.atm_intelligence.delta_battle_direction}"
        )
    
    def _generate_strategy_signal(self):
        """
        Generate clean strategy signal from Greeks
        Only exposes: direction_bias, acceleration_score, theta_pressure, volatility_state
        """
        signal = StrategySignal(timestamp=datetime.now())
        
        # -------- Health Check --------
        health = self.health_monitor.check_health(self.current_greeks, self.underlying or "")
        signal.is_data_healthy = health.can_trade
        
        if not signal.is_data_healthy:
            signal.is_tradeable = False
            signal.trade_recommendation = "AVOID"
            signal.confidence = 0.0
            logger.warning(f"Data unhealthy, blocking signal: {health.status.value}")
            self.current_signal = signal
            self._notify_signal_subscribers(signal)
            return
        
        # -------- Direction Bias (CE vs PE Delta) --------
        atm_ce_delta = 0.5
        atm_pe_delta = -0.5
        
        for strike, greek in self.current_greeks.items():
            if abs(strike - self.atm_strike) < 1.0:
                if greek.option_type == OptionType.CALL:
                    atm_ce_delta = greek.delta
                else:
                    atm_pe_delta = greek.delta
        
        # Normalize to 0-1 scale (0=bearish, 0.5=neutral, 1=bullish)
        combined_delta = atm_ce_delta + abs(atm_pe_delta)  # 0-2 scale
        signal.direction_bias = combined_delta / 2.0  # Convert to 0-1
        
        # -------- Acceleration Score (Gamma) --------
        if self.atm_intelligence and self.atm_intelligence.gamma_peak_value > 0:
            signal.acceleration_score = min(
                self.atm_intelligence.gamma_peak_value / 0.1, 1.0
            )
        
        # -------- Theta Pressure --------
        if self.atm_intelligence and self.atm_intelligence.theta_kill_value > 0:
            signal.theta_pressure = min(
                self.atm_intelligence.theta_kill_value / 2.0, 1.0
            )
        
        # -------- Volatility State --------
        signal.volatility_state = self.health_monitor.detect_iv_state(self.current_greeks)
        
        # -------- OI Sync Validation --------
        if self.previous_greeks and self.previous_oi_data:
            sync_result = self.oi_sync_validator.validate_chain_sync(
                self.current_greeks,
                self.previous_greeks,
                self.current_oi_data,
                self.previous_oi_data
            )
            
            signal.fake_move_detected = sync_result["fake_move_count"] > 0
            
            if sync_result["recommendation"] == "AVOID":
                signal.is_tradeable = False
                signal.trade_recommendation = "AVOID"
                signal.confidence = 0.1
                self.fake_moves_blocked += 1
                logger.warning("Fake move detected, blocking trade")
            elif sync_result["recommendation"] == "PROCEED":
                signal.is_tradeable = True
                signal.confidence = min(sync_result["overall_alignment"], 1.0)
            else:
                signal.is_tradeable = True
                signal.confidence = 0.5
        
        # -------- Trade Recommendation --------
        if not signal.is_tradeable:
            signal.trade_recommendation = "AVOID"
        else:
            # Simple logic: direction_bias biased enough + low theta + not fake
            if signal.direction_bias > 0.6:
                signal.trade_recommendation = "BUY_CALL"
            elif signal.direction_bias < 0.4:
                signal.trade_recommendation = "BUY_PUT"
            else:
                signal.trade_recommendation = "NEUTRAL"
            
            # Reduce confidence if theta_pressure high
            if signal.theta_pressure > 0.7:
                signal.confidence *= 0.5
                signal.trade_recommendation = "NEUTRAL"
        
        self.current_signal = signal
        self.signal_count += 1
        
        logger.info(
            f"Signal generated: bias={signal.direction_bias:.2f}, "
            f"accel={signal.acceleration_score:.2f}, "
            f"theta={signal.theta_pressure:.2f}, "
            f"rec={signal.trade_recommendation}, "
            f"conf={signal.confidence:.2f}"
        )
        
        self._notify_signal_subscribers(signal)
    
    # -------- Clean Interface for Strategy --------
    
    def get_direction_bias(self) -> float:
        """Get direction bias (0=bearish, 0.5=neutral, 1=bullish)"""
        if self.current_signal:
            return self.current_signal.direction_bias
        return 0.5
    
    def get_acceleration_score(self) -> float:
        """Get acceleration score (Gamma expansion level) [0-1]"""
        if self.current_signal:
            return self.current_signal.acceleration_score
        return 0.5
    
    def get_theta_pressure(self) -> float:
        """Get Theta decay pressure [0=safe, 1=danger zone]"""
        if self.current_signal:
            return self.current_signal.theta_pressure
        return 0.0
    
    def get_volatility_state(self) -> VolatilityState:
        """Get IV state (CRUSHING, STABLE_LOW, SURGING, etc.)"""
        if self.current_signal:
            return self.current_signal.volatility_state
        return VolatilityState.STABLE_MID
    
    def is_tradeable(self) -> bool:
        """True if Greeks data is healthy and no fake moves detected"""
        if self.current_signal:
            return self.current_signal.is_tradeable
        return False
    
    def get_trade_recommendation(self) -> str:
        """Get recommendation (BUY_CALL, BUY_PUT, AVOID, NEUTRAL)"""
        if self.current_signal:
            return self.current_signal.trade_recommendation
        return "NEUTRAL"
    
    def get_confidence(self) -> float:
        """Get confidence in current signal [0-1]"""
        if self.current_signal:
            return self.current_signal.confidence
        return 0.0
    
    def get_atm_intelligence(self) -> Optional[AtmIntelligence]:
        """Get ATM zone intelligence (gamma peak, theta kill zone, etc.)"""
        return self.atm_intelligence
    
    def get_current_signal(self) -> Optional[StrategySignal]:
        """Get complete strategy signal object"""
        return self.current_signal
    
    # -------- Subscription System --------
    
    def subscribe_to_signals(self, callback: Callable[[StrategySignal], None]):
        """Subscribe to strategy signals"""
        self.signal_callbacks.append(callback)
        logger.info(f"Signal subscriber registered ({len(self.signal_callbacks)} total)")
    
    def unsubscribe_from_signals(self, callback: Callable):
        """Unsubscribe from signals"""
        if callback in self.signal_callbacks:
            self.signal_callbacks.remove(callback)
    
    def _notify_signal_subscribers(self, signal: StrategySignal):
        """Notify all subscribers of new signal"""
        for callback in self.signal_callbacks:
            try:
                callback(signal)
            except Exception as e:
                logger.error(f"Signal callback error: {e}")
    
    # -------- Metrics & Diagnostics --------
    
    def get_metrics(self) -> Dict:
        """Get comprehensive metrics"""
        return {
            "greeks_signals_generated": self.signal_count,
            "fake_moves_blocked": self.fake_moves_blocked,
            "theta_exits_triggered": self.theta_exits_triggered,
            "calculator_metrics": self.calculator.get_metrics(),
            "oi_sync_metrics": self.oi_sync_validator.get_metrics(),
            "health_summary": self.health_monitor.get_health_summary(),
            "current_data_count": len(self.current_greeks)
        }
    
    def get_detailed_status(self) -> Dict:
        """Get detailed engine status"""
        return {
            "universe": {
                "underlying": self.underlying,
                "atm_strike": self.atm_strike,
                "days_to_expiry": self.days_to_expiry
            },
            "greeks_count": len(self.current_greeks),
            "atm_intelligence": self.atm_intelligence,
            "current_signal": self.current_signal,
            "health_status": self.health_monitor.get_health_summary(),
            "metrics": self.get_metrics()
        }
    
    def __repr__(self) -> str:
        """String representation"""
        status = "READY" if self.is_tradeable() else "CAUTIOUS"
        signal = self.get_trade_recommendation()
        bias = f"{self.get_direction_bias():.2f}"
        return (
            f"GreeksEngine({self.underlying} "
            f"bias={bias} rec={signal} status={status})"
        )
