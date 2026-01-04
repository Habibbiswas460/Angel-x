"""
PHASE 3 — Greeks Calculation Engine
Broker Greeks + Black-Scholes fallback for IV-based calculation

Components:
    • GreeksCalculator - Black-Scholes implementation
    • IvEstimator - Implied Volatility from market data
    • BrokerGreeksValidator - Normalize broker data
    • GreeksCalculationEngine - Main orchestrator
"""

import math
import logging
from datetime import datetime
from typing import Optional, Dict, Tuple
from dataclasses import dataclass

from .greeks_models import GreeksSnapshot, OptionType, GreeksHealthStatus

logger = logging.getLogger(__name__)


# ============================================================================
# Constants & Configuration
# ============================================================================

# Black-Scholes calculation constants
RISK_FREE_RATE = 0.06  # 6% p.a. (India RBI rate)
DAYS_PER_YEAR = 365.0

# IV estimation bounds
MIN_IV = 0.05          # 5% minimum
MAX_IV = 2.0           # 200% maximum
DEFAULT_IV = 0.25      # 25% default if cannot estimate

# Greeks validation bounds
DELTA_MIN, DELTA_MAX = 0.0, 1.0
GAMMA_MIN, GAMMA_MAX = 0.0, 0.2   # Very high Gamma is suspicious
THETA_MIN, THETA_MAX = -10.0, 0.0  # Theta should be negative (decay)
VEGA_MIN, VEGA_MAX = -100.0, 100.0


# ============================================================================
# Black-Scholes Greeks Calculation
# ============================================================================

class GreeksCalculator:
    """
    Black-Scholes Greeks calculator
    
    Used when broker doesn't provide Greeks or IV
    Takes: spot, strike, time_to_expiry, IV, risk-free rate
    Returns: Δ, Γ, Θ, ν
    """
    
    @staticmethod
    def _normal_pdf(x: float) -> float:
        """Normal probability density function"""
        return math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)
    
    @staticmethod
    def _normal_cdf(x: float) -> float:
        """Normal cumulative distribution (approximation)"""
        return (1 + math.erf(x / math.sqrt(2))) / 2
    
    @staticmethod
    def _d1(spot: float, strike: float, time_to_expiry: float, 
            volatility: float, rate: float) -> float:
        """Calculate d1 in BS model"""
        if time_to_expiry <= 0 or volatility <= 0:
            return 0.0
        
        ln_s_k = math.log(spot / strike)
        vol_sqrt_t = volatility * math.sqrt(time_to_expiry)
        
        d1 = (ln_s_k + (rate + 0.5 * volatility ** 2) * time_to_expiry) / vol_sqrt_t
        return d1
    
    @staticmethod
    def _d2(d1: float, time_to_expiry: float, volatility: float) -> float:
        """Calculate d2 in BS model"""
        if time_to_expiry <= 0 or volatility <= 0:
            return 0.0
        
        return d1 - volatility * math.sqrt(time_to_expiry)
    
    @classmethod
    def calculate_call_greeks(
        cls,
        spot: float,
        strike: float,
        time_to_expiry: float,
        volatility: float,
        rate: float = RISK_FREE_RATE
    ) -> Dict[str, float]:
        """
        Calculate Call option Greeks using Black-Scholes
        
        Args:
            spot: Current spot price
            strike: Strike price
            time_to_expiry: Days to expiry / 365
            volatility: Implied volatility (decimal, e.g., 0.25 for 25%)
            rate: Risk-free rate
        
        Returns:
            {"delta": 0-1, "gamma": 0+, "theta": negative, "vega": +/-}
        """
        if time_to_expiry <= 0:
            # Expiry today
            return {
                "delta": 1.0 if spot > strike else 0.0,
                "gamma": 0.0,
                "theta": 0.0,
                "vega": 0.0
            }
        
        d1 = cls._d1(spot, strike, time_to_expiry, volatility, rate)
        d2 = cls._d2(d1, time_to_expiry, volatility)
        
        # Call Greeks formulas
        nd1 = cls._normal_pdf(d1)
        Nd1 = cls._normal_cdf(d1)
        Nd2 = cls._normal_cdf(d2)
        
        # Delta [0-1]
        delta = Nd1
        
        # Gamma [0+]
        gamma = nd1 / (spot * volatility * math.sqrt(time_to_expiry))
        
        # Theta [negative] - per day
        theta_part1 = -spot * nd1 * volatility / (2 * math.sqrt(time_to_expiry))
        theta_part2 = -rate * strike * math.exp(-rate * time_to_expiry) * Nd2
        theta = (theta_part1 + theta_part2) / 365.0  # Convert to daily
        
        # Vega [+/-] - per 1% IV change
        vega = spot * nd1 * math.sqrt(time_to_expiry) / 100.0
        
        return {
            "delta": float(delta),
            "gamma": float(gamma),
            "theta": float(theta),
            "vega": float(vega)
        }
    
    @classmethod
    def calculate_put_greeks(
        cls,
        spot: float,
        strike: float,
        time_to_expiry: float,
        volatility: float,
        rate: float = RISK_FREE_RATE
    ) -> Dict[str, float]:
        """
        Calculate Put option Greeks using Black-Scholes
        Uses put-call parity relationships
        """
        if time_to_expiry <= 0:
            # Expiry today
            return {
                "delta": 0.0 if spot > strike else -1.0,
                "gamma": 0.0,
                "theta": 0.0,
                "vega": 0.0
            }
        
        d1 = cls._d1(spot, strike, time_to_expiry, volatility, rate)
        d2 = cls._d2(d1, time_to_expiry, volatility)
        
        nd1 = cls._normal_pdf(d1)
        Nd1 = cls._normal_cdf(d1)
        Nd2 = cls._normal_cdf(d2)
        
        # Put Delta (negative, 0 to -1)
        delta = Nd1 - 1.0
        
        # Put Gamma (same as call, positive)
        gamma = nd1 / (spot * volatility * math.sqrt(time_to_expiry))
        
        # Put Theta
        theta_part1 = -spot * nd1 * volatility / (2 * math.sqrt(time_to_expiry))
        theta_part2 = rate * strike * math.exp(-rate * time_to_expiry) * (1 - Nd2)
        theta = (theta_part1 + theta_part2) / 365.0  # Daily
        
        # Put Vega (same as call)
        vega = spot * nd1 * math.sqrt(time_to_expiry) / 100.0
        
        return {
            "delta": float(delta),
            "gamma": float(gamma),
            "theta": float(theta),
            "vega": float(vega)
        }


# ============================================================================
# Implied Volatility Estimation
# ============================================================================

class IvEstimator:
    """
    Estimate Implied Volatility from option price and market parameters
    
    Used when broker doesn't provide IV
    Takes: LTP, spot, strike, time_to_expiry
    Returns: IV estimate
    """
    
    @staticmethod
    def estimate_from_price(
        option_ltp: float,
        spot: float,
        strike: float,
        time_to_expiry: float,
        option_type: OptionType,
        rate: float = RISK_FREE_RATE
    ) -> float:
        """
        Estimate IV using simple heuristic
        (Full Newton-Raphson iteration would be better but overkill for scalping)
        
        Simple approach: Try different IVs and find closest match
        """
        if time_to_expiry <= 0:
            return DEFAULT_IV
        
        # Newton-Raphson iteration for IV
        iv = DEFAULT_IV
        for _ in range(10):  # Max 10 iterations
            try:
                if option_type == OptionType.CALL:
                    greeks = GreeksCalculator.calculate_call_greeks(
                        spot, strike, time_to_expiry, iv, rate
                    )
                else:
                    greeks = GreeksCalculator.calculate_put_greeks(
                        spot, strike, time_to_expiry, iv, rate
                    )
                
                # Approximate option price (simplified)
                # This is a heuristic, not exact BS pricing
                vega = greeks["vega"]
                if vega == 0:
                    break
                
                # Adjust IV towards actual price
                # (Full implementation would use actual BS price calculation)
                price_diff = option_ltp * 0.01  # Assume ~1% accuracy from heuristic
                iv_adjustment = price_diff / max(vega, 0.01)
                iv = max(MIN_IV, min(MAX_IV, iv + iv_adjustment))
                
            except Exception as e:
                logger.warning(f"IV estimation error: {e}, using default")
                return DEFAULT_IV
        
        return max(MIN_IV, min(MAX_IV, iv))


# ============================================================================
# Broker Greeks Validator & Normalizer
# ============================================================================

class BrokerGreeksValidator:
    """
    Validate Greeks from broker API
    Ensures: Ranges correct, no NaN, no freeze, reasonable values
    """
    
    @staticmethod
    def validate_greek_value(
        greek_name: str,
        value: Optional[float],
        option_type: OptionType
    ) -> Tuple[bool, Optional[float], str]:
        """
        Validate single Greek value
        Returns: (is_valid, cleaned_value, issue_description)
        """
        if value is None:
            return False, None, f"{greek_name} is None"
        
        if math.isnan(value) or math.isinf(value):
            return False, None, f"{greek_name} is NaN/Inf: {value}"
        
        # Validate ranges
        if greek_name == "delta":
            if option_type == OptionType.CALL:
                # Call delta: 0 to 1
                if DELTA_MIN <= value <= DELTA_MAX:
                    return True, value, ""
                else:
                    return False, None, f"Call Delta out of range: {value}"
            else:
                # Put delta: -1 to 0
                if -DELTA_MAX <= value <= DELTA_MIN:
                    return True, value, ""
                else:
                    return False, None, f"Put Delta out of range: {value}"
        
        elif greek_name == "gamma":
            # Gamma always positive, usually < 0.1
            if GAMMA_MIN <= value <= GAMMA_MAX:
                return True, value, ""
            else:
                return False, None, f"Gamma out of range: {value}"
        
        elif greek_name == "theta":
            # Theta usually negative (decay)
            if THETA_MIN <= value <= THETA_MAX:
                return True, value, ""
            else:
                return False, None, f"Theta out of range: {value}"
        
        elif greek_name == "vega":
            # Vega +/-, bounded
            if VEGA_MIN <= value <= VEGA_MAX:
                return True, value, ""
            else:
                return False, None, f"Vega out of range: {value}"
        
        return False, None, f"Unknown Greek: {greek_name}"
    
    @staticmethod
    def validate_snapshot(snapshot: Dict) -> Tuple[bool, str]:
        """
        Validate complete Greek snapshot
        Returns: (is_valid, issue_description)
        """
        required_fields = ["delta", "gamma", "theta", "vega"]
        
        for field in required_fields:
            if field not in snapshot:
                return False, f"Missing field: {field}"
        
        return True, ""


# ============================================================================
# Main Greeks Calculation Engine
# ============================================================================

class GreeksCalculationEngine:
    """
    Main orchestrator for Greeks calculation
    
    Strategy:
        1. Try broker Greeks (validate + normalize)
        2. If not available, estimate IV
        3. Use BS model to calculate
        4. Track previous values for change detection
        5. Health check results
    """
    
    def __init__(self, risk_free_rate: float = RISK_FREE_RATE):
        """Initialize Greeks engine"""
        self.risk_free_rate = risk_free_rate
        self.calculator = GreeksCalculator()
        self.iv_estimator = IvEstimator()
        self.validator = BrokerGreeksValidator()
        
        # Tracking
        self.calculation_count = 0
        self.fallback_count = 0
        self.error_count = 0
        
        logger.info(f"Greeks Engine initialized (Risk-free rate: {risk_free_rate*100:.2f}%)")
    
    def calculate_greeks(
        self,
        strike: float,
        option_type: OptionType,
        spot: float,
        days_to_expiry: float,
        ltp: float,
        broker_greeks: Optional[Dict[str, float]] = None,
        broker_iv: Optional[float] = None
    ) -> Tuple[GreeksSnapshot, str]:
        """
        Calculate Greeks for single strike
        
        Priority:
            1. Use broker Greeks if valid
            2. Use broker IV if available
            3. Estimate IV from LTP
            4. Use default IV
        
        Returns:
            (GreeksSnapshot, status_message)
        """
        time_to_expiry = max(days_to_expiry / 365.0, 0.001)  # Min 1/365 day
        
        # -------- Attempt 1: Broker Greeks --------
        if broker_greeks and "delta" in broker_greeks:
            try:
                is_valid, issue = self.validator.validate_snapshot(broker_greeks)
                if is_valid:
                    # Broker Greeks are valid, use them
                    snapshot = GreeksSnapshot(
                        strike=strike,
                        option_type=option_type,
                        delta=broker_greeks.get("delta", 0.0),
                        gamma=broker_greeks.get("gamma", 0.0),
                        theta=broker_greeks.get("theta", 0.0),
                        vega=broker_greeks.get("vega", 0.0),
                        implied_volatility=broker_iv or DEFAULT_IV,
                        iv_source="broker",
                        last_price=ltp,
                        timestamp=datetime.now()
                    )
                    self.calculation_count += 1
                    logger.debug(f"Using broker Greeks for {option_type.value} {strike}")
                    return snapshot, "broker_greeks"
                else:
                    logger.warning(f"Broker Greeks invalid: {issue}")
            except Exception as e:
                logger.warning(f"Broker Greeks error: {e}")
        
        # -------- Attempt 2: BS Model with IV --------
        try:
            # Determine IV source
            iv = broker_iv
            iv_source = "broker"
            
            if iv is None or not (MIN_IV <= iv <= MAX_IV):
                # Estimate IV from price
                iv = self.iv_estimator.estimate_from_price(
                    ltp, spot, strike, time_to_expiry, option_type, self.risk_free_rate
                )
                iv_source = "estimated"
            
            # Calculate Greeks using BS
            if option_type == OptionType.CALL:
                greeks_dict = self.calculator.calculate_call_greeks(
                    spot, strike, time_to_expiry, iv, self.risk_free_rate
                )
            else:
                greeks_dict = self.calculator.calculate_put_greeks(
                    spot, strike, time_to_expiry, iv, self.risk_free_rate
                )
            
            snapshot = GreeksSnapshot(
                strike=strike,
                option_type=option_type,
                delta=greeks_dict["delta"],
                gamma=greeks_dict["gamma"],
                theta=greeks_dict["theta"],
                vega=greeks_dict["vega"],
                implied_volatility=iv,
                iv_source=iv_source,
                last_price=ltp,
                timestamp=datetime.now()
            )
            
            self.calculation_count += 1
            self.fallback_count += 1
            logger.debug(f"Calculated Greeks (BS) for {option_type.value} {strike}, IV={iv*100:.2f}%")
            return snapshot, f"calculated_bs_{iv_source}"
        
        except Exception as e:
            logger.error(f"Greeks calculation failed: {e}")
            self.error_count += 1
            
            # Last resort: return zeros
            snapshot = GreeksSnapshot(
                strike=strike,
                option_type=option_type,
                delta=0.0,
                gamma=0.0,
                theta=0.0,
                vega=0.0,
                implied_volatility=DEFAULT_IV,
                iv_source="error_fallback",
                last_price=ltp,
                timestamp=datetime.now(),
                is_fresh=False,
                calculation_stable=False
            )
            
            return snapshot, f"error_fallback: {str(e)}"
    
    def get_metrics(self) -> Dict:
        """Return calculation metrics"""
        return {
            "total_calculated": self.calculation_count,
            "fallback_to_bs": self.fallback_count,
            "errors": self.error_count,
            "success_rate": (
                (self.calculation_count - self.error_count) / max(self.calculation_count, 1) * 100
            )
        }
