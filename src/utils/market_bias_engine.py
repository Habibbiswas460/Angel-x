"""
PHASE 5 — Market Bias & Trade Eligibility Engine (Main Orchestrator)

Combines all components:
1. Market Bias Constructor
2. Time Intelligence Gate
3. Volatility & Theta Guard
4. Trade Eligibility Engine
5. Direction & Strike Selector

Output: ExecutionSignal (dumb execution layer receives this)
"""

from typing import Optional, Dict, List
from datetime import datetime, time
import logging

from src.utils.market_bias_models import (
    Phase5Config, ExecutionSignal, BiasType, DirectionType,
    DataHealthStatus, Phase5Metrics, Phase5HealthReport,
)
from src.utils.market_bias_constructor import MarketBiasConstructor
from src.utils.time_and_greeks_gate import CombinedTimeAndGreeksGate
from src.utils.strike_selector import (
    TradeEligibilityEngine, DirectionAndStrikeSelector
)

logger = logging.getLogger(__name__)


class MarketBiasAndEligibilityEngine:
    """
    Phase 5 Main Orchestrator - Final Decision Gate
    
    Flow:
    1. Construct market bias (Bull/Bear/Neutral)
    2. Check time window & Greeks safety
    3. Run eligibility checks (5 gates)
    4. Select direction & strike
    5. Generate ExecutionSignal
    """
    
    def __init__(self, config: Phase5Config = None):
        self.config = config or Phase5Config()
        
        # Initialize components
        self.bias_constructor = MarketBiasConstructor(config)
        self.time_and_greeks_gate = CombinedTimeAndGreeksGate(config)
        self.eligibility_engine = TradeEligibilityEngine(config)
        self.strike_selector = DirectionAndStrikeSelector(config)
        
        # State
        self.current_bias = None
        self.current_eligibility = None
        self.current_signal = None
        self.universe_set = False
        self.atm_strike = None
        self.days_to_expiry = None
        
        # Metrics & diagnostics
        self.metrics = Phase5Metrics()
        self.signal_count = 0
        self.last_signal_time = None
    
    def set_universe(self, underlying: str, atm_strike: float, days_to_expiry: float):
        """Configure market universe"""
        self.underlying = underlying
        self.atm_strike = atm_strike
        self.days_to_expiry = days_to_expiry
        self.universe_set = True
        logger.info(f"Phase 5 universe set: {underlying} ATM={atm_strike} DTE={days_to_expiry}")
    
    def generate_signal(
        self,
        # Market data
        ce_dominance: float,           # [0-1] from Phase 4
        delta_ce: float,               # CE delta
        delta_pe: float,               # PE delta
        gamma_ce: float,               # CE gamma
        gamma_pe: float,               # PE gamma
        theta_ce: float,               # CE theta
        theta_pe: float,               # PE theta (previous)
        theta_ce_prev: float,          # CE theta previous
        theta_pe_prev: float,          # PE theta previous
        iv_current: float,             # Current IV
        iv_previous: float,            # Previous IV
        oi_conviction: float,          # From Phase 4
        volume_aggression: float,      # From Phase 4
        trap_probability: float,       # From Phase 4
        primary_buildup: Optional[str] = None,  # From Phase 4
        
        # Strike data for selection
        ce_atm_gamma: Optional[float] = None,
        ce_atm_fresh_oi: Optional[float] = None,
        ce_atm_volume: Optional[float] = None,
        ce_atm_plus1_gamma: Optional[float] = None,
        ce_atm_plus1_fresh_oi: Optional[float] = None,
        ce_atm_plus1_volume: Optional[float] = None,
        pe_atm_gamma: Optional[float] = None,
        pe_atm_fresh_oi: Optional[float] = None,
        pe_atm_volume: Optional[float] = None,
        pe_atm_minus1_gamma: Optional[float] = None,
        pe_atm_minus1_fresh_oi: Optional[float] = None,
        pe_atm_minus1_volume: Optional[float] = None,
        
        # Timing
        current_time: Optional[time] = None,
        data_health: DataHealthStatus = DataHealthStatus.GREEN,
        data_age_seconds: float = 0.0,
    ) -> ExecutionSignal:
        """
        Generate execution signal through full pipeline
        
        Returns ExecutionSignal with trade decision
        """
        
        if not self.universe_set:
            raise ValueError("Universe not set. Call set_universe() first.")
        
        # Use current time if not provided
        if current_time is None:
            current_time = datetime.now().time()
        
        # STEP 1: Detect market bias
        bias_analysis = self.bias_constructor.detect_bias(
            ce_dominance=ce_dominance,
            delta_ce=delta_ce,
            delta_pe=delta_pe,
            gamma_ce=gamma_ce,
            gamma_pe=gamma_pe,
            oi_conviction=oi_conviction,
            volume_aggression=volume_aggression,
            primary_buildup=primary_buildup,
        )
        
        self.current_bias = bias_analysis
        
        # STEP 2: Check time window & Greeks safety
        time_window, time_allowed, time_reason = self.time_and_greeks_gate.time_gate.analyze_time_window(current_time)
        
        theta_alert = self.time_and_greeks_gate.theta_guard.analyze_theta_velocity(
            theta_current=min(theta_ce, theta_pe),  # Use worse theta
            theta_previous=min(theta_ce_prev, theta_pe_prev),
            gamma_current=max(gamma_ce, gamma_pe),  # Use better gamma
            iv_current=iv_current,
            iv_previous=iv_previous,
        )
        
        greeks_safe = theta_alert.safe_to_trade
        
        # STEP 3: Run eligibility checks
        eligibility = self.eligibility_engine.check_eligibility(
            bias_type=bias_analysis.bias_type,
            bias_strength=bias_analysis.bias_strength,
            time_window=time_window,
            trap_probability=trap_probability,
            data_health=data_health,
            data_age_seconds=data_age_seconds,
            time_allowed=time_allowed,
            greeks_safe=greeks_safe,
        )
        
        self.current_eligibility = eligibility
        
        # STEP 4: Select direction & strike if eligible
        direction_selection = None
        if eligibility.trade_eligible:
            direction_selection = self.strike_selector.select_direction_and_strike(
                bias_type=bias_analysis.bias_type,
                atm_strike=self.atm_strike,
                # CE data
                ce_atm_gamma=ce_atm_gamma or gamma_ce,
                ce_atm_fresh_oi=ce_atm_fresh_oi or 0.0,
                ce_atm_volume=ce_atm_volume or 0.0,
                ce_atm_plus1_gamma=ce_atm_plus1_gamma,
                ce_atm_plus1_fresh_oi=ce_atm_plus1_fresh_oi,
                ce_atm_plus1_volume=ce_atm_plus1_volume,
                # PE data
                pe_atm_gamma=pe_atm_gamma or gamma_pe,
                pe_atm_fresh_oi=pe_atm_fresh_oi or 0.0,
                pe_atm_volume=pe_atm_volume or 0.0,
                pe_atm_minus1_gamma=pe_atm_minus1_gamma,
                pe_atm_minus1_fresh_oi=pe_atm_minus1_fresh_oi,
                pe_atm_minus1_volume=pe_atm_minus1_volume,
            )
        
        # STEP 5: Create execution signal
        signal = self._create_execution_signal(
            eligible=eligibility.trade_eligible,
            bias_analysis=bias_analysis,
            eligibility=eligibility,
            direction_selection=direction_selection,
            time_window=time_window,
            block_reason=eligibility.block_reason,
        )
        
        self.current_signal = signal
        self.signal_count += 1
        self.last_signal_time = datetime.now()
        
        # Update metrics
        self._update_metrics(bias_analysis, eligibility, signal)
        
        return signal
    
    def _create_execution_signal(
        self,
        eligible: bool,
        bias_analysis,
        eligibility,
        direction_selection,
        time_window,
        block_reason,
    ) -> ExecutionSignal:
        """Create ExecutionSignal for dumb execution layer"""
        
        if eligible and direction_selection:
            direction = direction_selection.direction
            strike_offset = direction_selection.strike_offset
            confidence = direction_selection.reason.weighted_score
            reasoning = direction_selection.reason.selection_reason
        else:
            direction = DirectionType.NEUTRAL
            strike_offset = 0
            confidence = 0.0
            reasoning = "Trade blocked"
        
        signal = ExecutionSignal(
            trade_allowed=eligible,
            direction=direction,
            strike_offset=strike_offset,
            confidence_level=confidence,
            conviction_category=bias_analysis.bias_strength.value,
            market_bias=bias_analysis.bias_type,
            bias_strength=bias_analysis.bias_strength,
            time_window=time_window,
            signal_id=f"PHASE5_{self.signal_count}",
            timestamp=datetime.now(),
            reasoning_brief=reasoning,
            fresh_position_active=False,  # Would come from Phase 4
            oi_conviction_score=bias_analysis.oi_conviction,
            volume_aggression_score=bias_analysis.volume_aggression,
            trap_probability=eligibility.trap_check.score,  # Actually trap prob
            block_reason=block_reason,
        )
        
        return signal
    
    def _update_metrics(self, bias_analysis, eligibility, signal):
        """Update diagnostic metrics"""
        
        # Bias distribution
        bias_key = bias_analysis.bias_type.value
        if bias_key not in self.metrics.bias_distribution:
            self.metrics.bias_distribution[bias_key] = 0
        self.metrics.bias_distribution[bias_key] += 1
        
        # Strength distribution
        strength_key = bias_analysis.bias_strength.value
        if strength_key not in self.metrics.strength_distribution:
            self.metrics.strength_distribution[strength_key] = 0
        self.metrics.strength_distribution[strength_key] += 1
        
        # Eligibility tracking
        if signal.trade_allowed:
            self.metrics.trades_allowed += 1
        else:
            self.metrics.trades_blocked += 1
            if not eligibility.bias_check.passed:
                self.metrics.blocked_due_to_bias += 1
            elif not eligibility.strength_check.passed:
                self.metrics.blocked_due_to_strength += 1
            elif not eligibility.time_check.passed:
                self.metrics.blocked_due_to_time += 1
            elif not eligibility.trap_check.passed:
                self.metrics.blocked_due_to_trap += 1
            elif not eligibility.data_health_check.passed:
                self.metrics.blocked_due_to_data_health += 1
        
        # Pass rate
        total = self.metrics.trades_allowed + self.metrics.trades_blocked
        if total > 0:
            self.metrics.eligibility_pass_rate = self.metrics.trades_allowed / total
    
    def get_current_signal(self) -> Optional[ExecutionSignal]:
        """Get latest execution signal"""
        return self.current_signal
    
    def get_metrics(self) -> Phase5Metrics:
        """Get diagnostic metrics"""
        return self.metrics
    
    def get_health_report(self) -> Phase5HealthReport:
        """Get overall engine health"""
        
        report = Phase5HealthReport(
            health_status="HEALTHY" if self.signal_count > 0 else "IDLE",
            bias_engine_ok=True,
            time_gate_ok=True,
            theta_guard_ok=True,
            eligibility_gate_ok=True,
            data_flow_ok=True,
            last_signal_time=self.last_signal_time,
            signals_processed=self.signal_count,
        )
        
        return report
    
    def get_detailed_status(self) -> Dict:
        """Get detailed status for debugging"""
        
        return {
            "universe_set": self.universe_set,
            "current_bias": self.current_bias.bias_type.value if self.current_bias else None,
            "bias_strength": self.current_bias.bias_strength.value if self.current_bias else None,
            "trade_eligible": self.current_eligibility.trade_eligible if self.current_eligibility else None,
            "last_signal_time": self.last_signal_time,
            "signals_processed": self.signal_count,
            "metrics": {
                "eligibility_pass_rate": f"{self.metrics.eligibility_pass_rate:.0%}",
                "trades_allowed": self.metrics.trades_allowed,
                "trades_blocked": self.metrics.trades_blocked,
                "bias_distribution": self.metrics.bias_distribution,
                "strength_distribution": self.metrics.strength_distribution,
            },
        }
    
    def reset(self):
        """Reset engine state"""
        self.current_bias = None
        self.current_eligibility = None
        self.current_signal = None
        self.metrics = Phase5Metrics()
        self.signal_count = 0
        self.last_signal_time = None
        self.bias_constructor.bias_history.clear()
        self.time_and_greeks_gate.theta_guard.reset()
        logger.info("Phase 5 engine reset")
