"""
PHASE 4 — SMART MONEY DETECTOR ENGINE
Main Orchestrator - All Components Integrated

Combines:
- OI Build-Up Classification (4 institutional states)
- Volume Spike Detection (sudden aggression)
- OI + Greeks Cross-Validation (truth table)
- CE vs PE Battlefield Analysis (ATM war)
- Fresh Position Detection (scalping edge)
- Fake Move & Trap Filter (risk gating)

Output: SmartMoneySignal (clean, simple, tradeable)

Philosophy:
Volume = Interest
OI = Commitment
Greeks = Risk Profile
→ All three together = TRADEABLE MOVE

Author: Angel-X Brain Layer
Date: January 4, 2026
Status: Production-Ready
"""

import logging
from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta

from .smart_money_models import (
    SmartMoneySignal,
    SmartMoneyMetrics,
    SmartMoneyHealthReport,
    SmartMoneyConfig,
    DetailedSmartMoneyStatus,
    BattlefieldControl,
    OiBuildUpType,
)
from .smart_money_oi_classifier import OiBuildUpClassifier
from .smart_money_volume_detector import VolumeSpikeDetector, ChainVolumeAnalyzer
from .smart_money_oi_greeks_validator import OiGreeksCrossValidator
from .smart_money_ce_pe_analyzer import CePeBattlefieldAnalyzer
from .smart_money_fresh_detector import FreshPositionDetector
from .smart_money_trap_filter import FakeMoveAndTrapFilter


logger = logging.getLogger(__name__)


class SmartMoneyDetector:
    """
    Main Smart Money Detection Engine

    Combines all Phase 4 components into single intelligence layer
    Converts raw market data (Phase 2B) + Greeks (Phase 3) into
    actionable smart money signals for strategy layer.

    Clean interface for strategy layer - no raw data exposed,
    only processed signals.
    """

    def __init__(self, config: Optional[SmartMoneyConfig] = None):
        """Initialize orchestrator with all components"""
        self.config = config or SmartMoneyConfig()

        # Components
        self.oi_classifier = OiBuildUpClassifier(config=self.config)
        self.volume_detector = VolumeSpikeDetector(config=self.config)
        self.chain_volume_analyzer = ChainVolumeAnalyzer(config=self.config)
        self.oi_greeks_validator = OiGreeksCrossValidator(config=self.config)
        self.battlefield_analyzer = CePeBattlefieldAnalyzer(config=self.config)
        self.fresh_detector = FreshPositionDetector(config=self.config)
        self.trap_filter = FakeMoveAndTrapFilter(config=self.config)

        # State
        self.underlying: Optional[str] = None
        self.atm_strike: Optional[float] = None
        self.days_to_expiry: Optional[float] = None

        self.current_signal: Optional[SmartMoneySignal] = None
        self.previous_Greeks: Dict[float, Dict] = {}
        self.current_greeks: Dict[float, Dict] = {}
        self.previous_oi: Dict[float, Dict] = {}
        self.current_oi: Dict[float, Dict] = {}

        # Signal subscribers
        self.signal_callbacks: List = []

        # Metrics
        self.update_count = 0
        self.last_update_time: Optional[datetime] = None

    def set_universe(
        self,
        underlying: str,
        atm_strike: float,
        days_to_expiry: float,
    ):
        """Set trading universe"""
        self.underlying = underlying
        self.atm_strike = atm_strike
        self.days_to_expiry = days_to_expiry

        logger.info(f"SmartMoneyDetector universe set: {underlying} @ {atm_strike}, " f"DTE={days_to_expiry:.1f}")

    def update_from_market_data(
        self,
        strikes_data: Dict[float, Dict],  # {strike: {"CE": {...}, "PE": {...}}, ...}
        greeks_data: Dict[float, Dict],  # From Phase 3 engine
        current_oi_data: Dict[float, Dict],  # {strike: {"CE": {oi, vol}, "PE": {...}}, ...}
    ) -> SmartMoneySignal:
        """
        Update engine with latest market data

        Input format:
        strikes_data: {
            19900: {
                "CE": {"ltp": 100, "volume": 500, "bid": 99, "ask": 101},
                "PE": {"ltp": 50, "volume": 400, "bid": 49, "ask": 51},
            },
            ...
        }

        greeks_data: {
            19900: {
                "CE": {
                    "delta": 0.3, "gamma": 0.02, "theta": -0.5, "vega": 0.1,
                    "implied_volatility": 0.25, "prev_delta": 0.25, ...
                },
                "PE": {...},
            },
            ...
        }

        current_oi_data: {
            19900: {
                "CE": {"oi": 1000, "volume": 500},
                "PE": {"oi": 800, "volume": 400},
            },
            ...
        }

        Returns: SmartMoneySignal
        """

        self.update_count += 1
        self.last_update_time = datetime.now()

        # Shift previous data
        self.previous_Greeks = self.current_greeks.copy()
        self.previous_oi = self.current_oi.copy()

        self.current_greeks = greeks_data.copy()
        self.current_oi = current_oi_data.copy()

        # Process each strike
        oi_classifications = {}
        volume_states = {}
        fresh_positions = []
        trap_detections = {}
        cross_validations = {}

        for strike in strikes_data.keys():
            strike_data = strikes_data[strike]

            # Process CE
            if "CE" in strike_data:
                self._process_strike_option(
                    strike=strike,
                    option_type="CE",
                    strike_data=strike_data["CE"],
                    greeks_data=greeks_data.get(strike, {}).get("CE", {}),
                    oi_data=current_oi_data.get(strike, {}).get("CE", {}),
                    oi_classifications=oi_classifications,
                    volume_states=volume_states,
                    fresh_positions=fresh_positions,
                    trap_detections=trap_detections,
                    cross_validations=cross_validations,
                )

            # Process PE
            if "PE" in strike_data:
                self._process_strike_option(
                    strike=strike,
                    option_type="PE",
                    strike_data=strike_data["PE"],
                    greeks_data=greeks_data.get(strike, {}).get("PE", {}),
                    oi_data=current_oi_data.get(strike, {}).get("PE", {}),
                    oi_classifications=oi_classifications,
                    volume_states=volume_states,
                    fresh_positions=fresh_positions,
                    trap_detections=trap_detections,
                    cross_validations=cross_validations,
                )

        # Analyze CE vs PE battlefield (ATM zone)
        atm_strikes = self._get_atm_zone_strikes()
        battlefield = self.battlefield_analyzer.analyze_battlefield(
            atm_strikes=atm_strikes,
            strikes_data=strikes_data,
        )

        # Generate signal
        signal = self._generate_signal(
            oi_classifications=oi_classifications,
            volume_states=volume_states,
            fresh_positions=fresh_positions,
            trap_detections=trap_detections,
            cross_validations=cross_validations,
            battlefield=battlefield,
        )

        self.current_signal = signal

        # Notify subscribers
        self._notify_subscribers(signal)

        logger.debug(
            f"SmartMoneyDetector update #{self.update_count}: "
            f"Recommendation={signal.recommendation}, "
            f"Can_Trade={signal.can_trade}"
        )

        return signal

    def get_current_signal(self) -> Optional[SmartMoneySignal]:
        """Get latest signal"""
        return self.current_signal

    def get_market_control(self) -> str:
        """Get current battlefield control status"""
        if not self.current_signal:
            return "NEUTRAL"

        control_map = {
            BattlefieldControl.BULLISH_CONTROL: "BULLISH",
            BattlefieldControl.BEARISH_CONTROL: "BEARISH",
            BattlefieldControl.NEUTRAL_CHOP: "CHOP",
            BattlefieldControl.BALANCED: "BALANCED",
        }

        return control_map.get(self.current_signal.market_control, "UNKNOWN")

    def get_oi_conviction(self) -> float:
        """Get OI conviction score (0-1)"""
        if not self.current_signal:
            return 0.0
        return self.current_signal.oi_conviction_score

    def get_volume_aggression(self) -> float:
        """Get volume aggression score (0-1)"""
        if not self.current_signal:
            return 0.0
        return self.current_signal.volume_aggression_score

    def get_smart_money_probability(self) -> float:
        """Get smart money move probability (0-1)"""
        if not self.current_signal:
            return 0.0
        return self.current_signal.smart_money_probability

    def get_trap_probability(self) -> float:
        """Get trap probability (0-1)"""
        if not self.current_signal:
            return 0.0
        return self.current_signal.trap_probability

    def is_fresh_position_active(self) -> bool:
        """Check if fresh position currently detected"""
        if not self.current_signal:
            return False
        return self.current_signal.fresh_position_detected

    def can_trade(self) -> bool:
        """Check if conditions allow trading"""
        if not self.current_signal:
            return False
        return self.current_signal.can_trade

    def get_recommendation(self) -> str:
        """Get trade recommendation"""
        if not self.current_signal:
            return "AVOID"
        return self.current_signal.recommendation

    def subscribe_to_signals(self, callback):
        """Subscribe to signal updates"""
        if callback not in self.signal_callbacks:
            self.signal_callbacks.append(callback)

    def unsubscribe_from_signals(self, callback):
        """Unsubscribe from signals"""
        if callback in self.signal_callbacks:
            self.signal_callbacks.remove(callback)

    def get_metrics(self) -> Dict:
        """Get aggregated metrics"""

        return {
            "update_count": self.update_count,
            "last_update": self.last_update_time.isoformat() if self.last_update_time else None,
            "oi_classifier": self.oi_classifier.get_metrics(),
            "volume_detector": self.volume_detector.get_metrics(),
            "oi_greeks_validator": self.oi_greeks_validator.get_metrics(),
            "battlefield_analyzer": self.battlefield_analyzer.get_metrics(),
            "fresh_detector": self.fresh_detector.get_metrics(),
            "trap_filter": self.trap_filter.get_metrics(),
        }

    def get_detailed_status(self) -> DetailedSmartMoneyStatus:
        """Get comprehensive diagnostic status"""

        data_old = False
        if self.last_update_time:
            age = (datetime.now() - self.last_update_time).total_seconds()
            data_old = age > self.config.max_data_age_seconds

        greeks_available = len(self.current_greeks) > 0
        oi_volume_available = len(self.current_oi) > 0

        health = self._check_health()

        return DetailedSmartMoneyStatus(
            is_ready=not data_old and greeks_available and oi_volume_available,
            health_status=health.status,
            data_freshness_ok=not data_old,
            greeks_data_available=greeks_available,
            oi_volume_data_available=oi_volume_available,
            strikes_analyzed=len(self.current_greeks),
            high_conviction_strikes=len(self.oi_classifier.get_high_conviction_strikes()),
            fresh_position_count=len(self.fresh_detector.get_fresh_positions_in_chain()),
            signal_confidence=(self.current_signal.smart_money_probability if self.current_signal else 0.0),
            alignment_score=self.oi_greeks_validator.get_metrics()["alignment_rate"] / 100,
            last_signal_timestamp=self.last_update_time or datetime.now(),
            last_signal_direction=(self.current_signal.recommendation if self.current_signal else ""),
            warnings=health.issues if health.status != "HEALTHY" else [],
            errors=[],
            config=self.config,
        )

    def reset(self):
        """Reset all components"""
        self.oi_classifier.reset()
        self.volume_detector.reset()
        self.chain_volume_analyzer.reset()
        self.oi_greeks_validator.reset()
        self.battlefield_analyzer.reset()
        self.fresh_detector.reset()
        self.trap_filter.reset()

        self.current_signal = None
        self.previous_Greeks.clear()
        self.current_greeks.clear()
        self.previous_oi.clear()
        self.current_oi.clear()

        self.update_count = 0
        self.last_update_time = None

    # ========================================================================
    # PRIVATE HELPERS
    # ========================================================================

    def _process_strike_option(
        self,
        strike: float,
        option_type: str,
        strike_data: Dict,
        greeks_data: Dict,
        oi_data: Dict,
        oi_classifications: Dict,
        volume_states: Dict,
        fresh_positions: List,
        trap_detections: Dict,
        cross_validations: Dict,
    ):
        """Process single strike option through all components"""

        # Extract data
        ltp = strike_data.get("ltp", 0)
        volume = strike_data.get("volume", 0)
        prev_ltp = self.previous_Greeks.get(strike, {}).get(option_type, {}).get("ltp", 0)
        prev_volume = self.previous_oi.get(strike, {}).get(option_type, {}).get("volume", 0)

        oi = oi_data.get("oi", 0)
        prev_oi = self.previous_oi.get(strike, {}).get(option_type, {}).get("oi", 0)

        # Greeks
        delta = greeks_data.get("delta", 0)
        gamma = greeks_data.get("gamma", 0)
        theta = greeks_data.get("theta", 0)
        prev_delta = greeks_data.get("prev_delta", 0)
        prev_gamma = greeks_data.get("prev_gamma", 0)
        prev_theta = greeks_data.get("prev_theta", 0)

        # 1. OI Classification
        buildup_type, confidence = self.oi_classifier.classify_strike(
            strike=strike,
            option_type=option_type,
            current_price=ltp,
            previous_price=prev_ltp,
            current_oi=oi,
            previous_oi=prev_oi if prev_oi > 0 else None,
            current_volume=volume,
            previous_volume=prev_volume if prev_volume > 0 else None,
        )

        key = (strike, option_type)
        oi_classifications[key] = {
            "type": buildup_type,
            "confidence": confidence,
        }

        # 2. Volume Detection
        volume_state, spike_factor = self.volume_detector.detect_volume_spike(
            strike=strike,
            option_type=option_type,
            current_volume=volume,
        )

        volume_states[key] = {
            "state": volume_state,
            "spike_factor": spike_factor,
        }

        # 3. Fresh Position Detection
        avg_vol = self.volume_detector.get_average_volume(strike, option_type)
        fresh_signal = self.fresh_detector.detect_fresh_position(
            strike=strike,
            option_type=option_type,
            current_oi=oi,
            previous_oi=prev_oi if prev_oi > 0 else None,
            current_volume=volume,
            previous_volume=prev_volume if prev_volume > 0 else None,
            avg_volume=avg_vol,
        )

        if fresh_signal:
            fresh_positions.append((key, fresh_signal))

        # 4. Trap Detection
        price_change = (ltp - prev_ltp) / prev_ltp if prev_ltp > 0 else 0
        prev_price_change = None  # Would need more history

        trap_check = self.trap_filter.comprehensive_trap_check(
            oi=oi,
            previous_oi=prev_oi if prev_oi > 0 else None,
            volume=volume,
            previous_volume=prev_volume if prev_volume > 0 else None,
            gamma=gamma,
            theta=theta,
            previous_theta=prev_theta if prev_theta != 0 else None,
            price_change=price_change,
            previous_price_change=prev_price_change,
            days_to_expiry=self.days_to_expiry or 1.0,
            strike_position=self._get_strike_position(strike),
        )

        trap_detections[key] = trap_check

        # 5. OI + Greeks Cross-Validation
        validation = self.oi_greeks_validator.validate_strike_alignment(
            strike=strike,
            delta=delta,
            gamma=gamma,
            theta=theta,
            vega=greeks_data.get("vega", 0),
            oi_change=(oi - prev_oi) / prev_oi if prev_oi > 0 else 0,
            volume_change=volume / prev_volume if prev_volume > 0 else 1.0,
            previous_delta=prev_delta if prev_delta != 0 else None,
            previous_gamma=prev_gamma if prev_gamma != 0 else None,
            previous_theta=prev_theta if prev_theta != 0 else None,
        )

        cross_validations[key] = validation

    def _generate_signal(
        self,
        oi_classifications: Dict,
        volume_states: Dict,
        fresh_positions: List,
        trap_detections: Dict,
        cross_validations: Dict,
        battlefield,
    ) -> SmartMoneySignal:
        """Generate final SmartMoneySignal from all analyses"""

        # Count high conviction OI
        high_conviction = sum(
            1
            for c in oi_classifications.values()
            if c["type"] in [OiBuildUpType.LONG_BUILD_UP, OiBuildUpType.SHORT_BUILD_UP]
        )
        total_strikes = len(oi_classifications)

        # OI conviction score
        oi_conviction = high_conviction / max(total_strikes, 1)

        # Volume aggression
        volume_spike_count = sum(1 for v in volume_states.values() if v["spike_factor"] > 1.5)
        volume_aggression = volume_spike_count / max(total_strikes, 1)

        # Trap probability
        trap_count = sum(1 for t in trap_detections.values() if t["is_trap"])
        trap_probability = trap_count / max(total_strikes, 1)

        # Fresh position
        fresh_detected = len(fresh_positions) > 0
        fresh_strength = max(f[1].confidence for f in fresh_positions) if fresh_positions else 0.0

        # Cross-validation alignment
        aligned_count = sum(1 for cv in cross_validations.values() if cv.get("aligned", False))
        alignment_rate = aligned_count / max(total_strikes, 1)

        # Direction determination
        if oi_conviction > 0.6 and high_conviction > 0:
            long_count = sum(1 for c in oi_classifications.values() if c["type"] == OiBuildUpType.LONG_BUILD_UP)
            short_count = sum(1 for c in oi_classifications.values() if c["type"] == OiBuildUpType.SHORT_BUILD_UP)

            if long_count > short_count:
                direction_bias = "BULLISH"
            elif short_count > long_count:
                direction_bias = "BEARISH"
            else:
                direction_bias = "NEUTRAL"
        else:
            direction_bias = "NEUTRAL"

        # Generate recommendation
        can_trade = oi_conviction > 0.5 and volume_aggression > 0.3 and trap_probability < 0.4 and alignment_rate > 0.6

        if not can_trade:
            recommendation = "AVOID"
        elif trap_detections and any(t["should_block"] for t in trap_detections.values()):
            recommendation = "AVOID"
        elif direction_bias == "BULLISH":
            recommendation = "BUY_CALL"
        elif direction_bias == "BEARISH":
            recommendation = "BUY_PUT"
        else:
            recommendation = "NEUTRAL"

        # Smart money probability
        smart_money_prob = (oi_conviction + volume_aggression + alignment_rate) / 3

        # Dominant strikes (high activity)
        dominant = [strike for (strike, opt_type), vol in volume_states.items() if vol["spike_factor"] > 2.0]

        # Create signal
        signal = SmartMoneySignal(
            market_control=battlefield.control,
            oi_conviction_score=oi_conviction,
            volume_aggression_score=volume_aggression,
            smart_money_probability=smart_money_prob,
            trap_probability=trap_probability,
            fake_move_probability=trap_probability,
            fresh_position_detected=fresh_detected,
            fresh_position_strength=fresh_strength,
            direction_bias=direction_bias,
            direction_confidence=oi_conviction,
            can_trade=can_trade,
            recommendation=recommendation,
            reason=self._generate_reason(
                direction_bias,
                can_trade,
                oi_conviction,
                trap_probability,
            ),
            timestamp=datetime.now(),
            data_age_seconds=int(
                (datetime.now() - self.last_update_time).total_seconds() if self.last_update_time else 0
            ),
            dominant_strikes=list(set(dominant)),
        )

        return signal

    def _get_atm_zone_strikes(self) -> List[float]:
        """Get strikes within ATM zone"""
        if not self.atm_strike:
            return []

        zone_range = self.config.ce_pe_atm_range
        return [s for s in self.current_greeks.keys() if abs(s - self.atm_strike) <= zone_range]

    def _get_strike_position(self, strike: float) -> str:
        """Determine if strike is ATM, OTM, or ITM"""
        if not self.atm_strike:
            return "UNKNOWN"

        diff = abs(strike - self.atm_strike)
        if diff <= 100:
            return "ATM"
        else:
            return "OTM"

    def _generate_reason(
        self,
        direction: str,
        can_trade: bool,
        conviction: float,
        trap_prob: float,
    ) -> str:
        """Generate explanation for signal"""

        if not can_trade:
            if trap_prob > 0.5:
                return "Trap detected - Low conviction setup"
            else:
                return "Insufficient signal strength"

        reason = f"{direction} bias with {conviction*100:.0f}% conviction"

        if trap_prob > 0.3:
            reason += f" (watch for traps, prob={trap_prob*100:.0f}%)"

        return reason

    def _check_health(self) -> SmartMoneyHealthReport:
        """Check engine health"""

        issues = []
        status = "HEALTHY"

        if not self.current_greeks:
            issues.append("No Greeks data available")
            status = "UNHEALTHY"

        if not self.current_oi:
            issues.append("No OI/Volume data available")
            status = "UNHEALTHY"

        if self.last_update_time:
            age = (datetime.now() - self.last_update_time).total_seconds()
            if age > self.config.max_data_age_seconds:
                issues.append(f"Data stale ({int(age)}s old)")
                status = "STALE"
            elif age > self.config.max_data_age_seconds * 0.5:
                issues.append(f"Data aging ({int(age)}s)")
                if status == "HEALTHY":
                    status = "DEGRADED"

        return SmartMoneyHealthReport(
            status=status,
            can_analyze=status == "HEALTHY",
            issues=issues,
            strikes_analyzed=len(self.current_greeks),
            strikes_with_volume=len([s for s in self.current_oi.values() if s.get("volume", 0) > 0]),
            strikes_with_oi=len([s for s in self.current_oi.values() if s.get("oi", 0) > 0]),
            max_data_age_seconds=int(
                (datetime.now() - self.last_update_time).total_seconds() if self.last_update_time else 0
            ),
        )

    def _notify_subscribers(self, signal: SmartMoneySignal):
        """Notify all subscribers of new signal"""
        for callback in self.signal_callbacks:
            try:
                callback(signal)
            except Exception as e:
                logger.error(f"Error notifying subscriber: {e}")
