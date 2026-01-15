"""
PHASE 6 — PRE-ORDER SAFETY GATE + POSITION SIZING ENGINE

1. Final checks before order placement
2. Fixed-risk position sizing
3. Stop-loss price calculation
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Tuple, Optional
from src.utils.trade_models import (
    Phase6Config,
    RiskLimitStatus,
    OrderPlacementRequest,
    TradeLevel,
    calculate_position_risk,
)


# ============================================================================
# PRE-ORDER SAFETY GATE
# ============================================================================


class PreOrderSafetyGate:
    """Final checks before order placement"""

    def __init__(self, config: Optional[Phase6Config] = None):
        self.config = config or Phase6Config()

    def can_place_order(
        self,
        current_time: datetime,
        risk_limits: RiskLimitStatus,
        active_positions: int = 0,
        market_open: bool = True,
        trade_allowed: bool = True,
    ) -> Tuple[bool, str, list]:
        """
        Final pre-order safety checks
        Returns: (can_trade, summary_reason, detailed_checks)
        """

        checks = []
        blocking = False

        # Check 1: Market is open
        check1 = market_open
        checks.append(("Market Open", check1))
        if not check1:
            blocking = True

        # Check 2: Trade signal is allowed
        check2 = trade_allowed
        checks.append(("Trade Allowed Signal", check2))
        if not check2:
            blocking = True

        # Check 3: No active position
        check3 = active_positions == 0
        checks.append(("No Active Position", check3))
        if not check3:
            blocking = True

        # Check 4: Risk limits OK
        can_trade, risk_msg = risk_limits.can_trade(current_time)
        checks.append(("Risk Limits OK", can_trade))
        if not can_trade:
            blocking = True

        # Check 5: Not in trading lock
        check5 = not risk_limits.trading_locked
        checks.append(("Not Trading Locked", check5))
        if not check5:
            blocking = True

        # Generate summary
        passed = sum(1 for _, result in checks if result)
        total = len(checks)
        summary = f"{passed}/{total} checks passed"

        if blocking:
            failed_checks = [name for name, result in checks if not result]
            reason = f"BLOCKED: {', '.join(failed_checks)}"
        else:
            reason = "All checks passed ✓"

        return not blocking, reason, checks

    def validate_order_request(
        self,
        request: OrderPlacementRequest,
    ) -> Tuple[bool, str]:
        """Validate order placement request"""

        # Quantity check
        if request.quantity < self.config.min_position_size:
            return False, f"Quantity {request.quantity} below minimum {self.config.min_position_size}"

        if request.quantity > self.config.max_position_size:
            return False, f"Quantity {request.quantity} above maximum {self.config.max_position_size}"

        # Price check
        if request.sl_price <= 0 or request.entry_price <= 0:
            return False, "Invalid prices (must be positive)"

        # SL distance check
        sl_distance = abs(request.entry_price - request.sl_price)

        if sl_distance < self.config.min_sl_distance_points:
            return False, f"SL too close ({sl_distance} < {self.config.min_sl_distance_points})"

        if sl_distance > self.config.max_sl_distance_points:
            return False, f"SL too far ({sl_distance} > {self.config.max_sl_distance_points})"

        return True, "Valid order request ✓"


# ============================================================================
# POSITION SIZING ENGINE (Fixed-Risk)
# ============================================================================


class PositionSizingEngine:
    """
    Calculate quantity based on fixed risk.
    Core principle: Risk is fixed, quantity is calculated
    """

    def __init__(self, config: Optional[Phase6Config] = None):
        self.config = config or Phase6Config()

    def calculate_quantity(
        self,
        entry_price: float,
        sl_price: float,
        risk_budget: Optional[float] = None,
        volatility_factor: float = 1.0,  # >1 = reduce quantity in high vol
    ) -> Tuple[int, float, str]:
        """
        Calculate quantity based on fixed risk

        Returns: (quantity, actual_risk, reason)
        """

        # Use configured risk if not specified
        risk_amount = risk_budget or self.config.fixed_risk_per_trade

        # Calculate point distance
        point_distance = abs(entry_price - sl_price)

        if point_distance < 0.01:
            return 0, 0.0, "SL distance too small"

        # Risk per point (in ₹)
        risk_per_point = 100  # 1 point = ₹100 per contract

        # Base quantity
        base_quantity = risk_amount / (point_distance * risk_per_point)

        # Apply volatility adjustment
        # High vol → reduce size (survive first)
        adjusted_quantity = base_quantity / volatility_factor

        # Round to integer
        quantity = max(int(adjusted_quantity), self.config.min_position_size)
        quantity = min(quantity, self.config.max_position_size)

        # Calculate actual risk at this quantity
        actual_risk = calculate_position_risk(entry_price, sl_price, quantity)

        # Reasoning
        reason = (
            f"Fixed Risk: ₹{risk_amount:.0f} | "
            f"SL Distance: {point_distance:.1f}pts | "
            f"Quantity: {quantity} | "
            f"Actual Risk: ₹{actual_risk:.0f}"
        )

        return quantity, actual_risk, reason

    def adjust_for_volatility(
        self,
        base_quantity: int,
        current_iv: float,
        iv_threshold: float = 0.25,
    ) -> Tuple[int, str]:
        """
        Reduce quantity if IV is high
        Philosophy: When volatility high, risk more → reduce size
        """

        if current_iv > iv_threshold:
            # High IV
            factor = min(current_iv / iv_threshold, 2.0)  # Max 50% reduction
            adjusted = max(int(base_quantity / factor), self.config.min_position_size)
            reason = f"IV high ({current_iv:.2f}), reduced from {base_quantity} to {adjusted}"
        else:
            # Normal IV
            adjusted = base_quantity
            reason = f"IV normal ({current_iv:.2f}), using {adjusted}"

        return adjusted, reason


# ============================================================================
# STOP-LOSS CALCULATION ENGINE
# ============================================================================


class StopLossCalculationEngine:
    """
    Calculate SL based on market structure, not arbitrary %.
    Options: Delta flip zone, Gamma exhaustion, Hard % SL (backup)
    """

    def __init__(self, config: Optional[Phase6Config] = None):
        self.config = config or Phase6Config()

    def calculate_sl_price(
        self,
        entry_price: float,
        delta_ce: Optional[float] = None,
        delta_pe: Optional[float] = None,
        gamma_ce: Optional[float] = None,
        gamma_pe: Optional[float] = None,
        option_type: str = "CE",
    ) -> Tuple[float, str, TradeLevel]:
        """
        Calculate SL price based on structure
        Priority: 1) Delta flip, 2) Gamma exhaustion, 3) Hard %
        """

        sl_price = None
        method = None

        # Method 1: Delta flip zone
        if delta_ce is not None and delta_pe is not None:
            if option_type == "CE":
                # For CE: SL at PE dominance zone (delta_ce becomes <0.3)
                # Estimate: Each 1 point, delta changes ~0.02-0.05
                # Conservative: need 10-15 points
                delta_flip_sl = entry_price - 15
                if delta_flip_sl > 0:
                    sl_price = delta_flip_sl
                    method = "Delta flip zone"
            elif option_type == "PE":
                # For PE: SL at CE dominance zone
                delta_flip_sl = entry_price + 15
                sl_price = delta_flip_sl
                method = "Delta flip zone"

        # Method 2: Gamma exhaustion (if delta not available)
        if sl_price is None and gamma_ce is not None and gamma_pe is not None:
            if gamma_ce > gamma_pe:
                # CE has better gamma support
                exhaustion_sl = entry_price - 10  # Conservative
            else:
                exhaustion_sl = entry_price + 10

            if exhaustion_sl > 0:
                sl_price = exhaustion_sl
                method = "Gamma exhaustion"

        # Method 3: Hard % SL (backup)
        if sl_price is None:
            hard_sl = entry_price * (1 - self.config.hard_sl_percent / 100)
            sl_price = max(hard_sl, 0)
            method = "Hard 2% SL"

        # Ensure minimum distance
        distance = abs(entry_price - sl_price)
        if distance < self.config.min_sl_distance_points:
            # Adjust SL further out
            if option_type == "CE":
                sl_price = entry_price - self.config.min_sl_distance_points
            else:
                sl_price = entry_price + self.config.min_sl_distance_points
            method += f" (adjusted to min distance {self.config.min_sl_distance_points}pts)"

        # Cap maximum distance
        if distance > self.config.max_sl_distance_points:
            if option_type == "CE":
                sl_price = entry_price - self.config.max_sl_distance_points
            else:
                sl_price = entry_price + self.config.max_sl_distance_points
            method += f" (capped to max distance {self.config.max_sl_distance_points}pts)"

        # Create TradeLevel
        trade_level = TradeLevel(
            price=sl_price,
            level_type="SL",
            reason=method,
            delta_at_level=delta_pe if option_type == "CE" else delta_ce,
        )

        return sl_price, method, trade_level


# ============================================================================
# TARGET CALCULATION ENGINE
# ============================================================================


class TargetCalculationEngine:
    """Calculate initial profit target"""

    def __init__(self, config: Optional[Phase6Config] = None):
        self.config = config or Phase6Config()

    def calculate_target_price(
        self,
        entry_price: float,
        option_type: str = "CE",
    ) -> Tuple[float, TradeLevel]:
        """
        Conservative target calculation
        CE: entry + target%, PE: entry - target%
        (For options, CE gains value when underlying goes up, PE when it goes down)
        """

        if option_type == "CE":
            target = entry_price + (entry_price * self.config.initial_target_percent / 100)
        else:
            target = entry_price - (entry_price * self.config.initial_target_percent / 100)

        target = max(target, 0)

        trade_level = TradeLevel(
            price=target,
            level_type="TARGET",
            reason=f"Conservative {self.config.initial_target_percent}% target",
        )

        return target, trade_level


# ============================================================================
# ORDER PREPARATION
# ============================================================================


class OrderPreparationEngine:
    """Prepare complete order with all calculations"""

    def __init__(
        self,
        config: Optional[Phase6Config] = None,
        safety_gate: Optional[PreOrderSafetyGate] = None,
        sizing_engine: Optional[PositionSizingEngine] = None,
        sl_engine: Optional[StopLossCalculationEngine] = None,
        target_engine: Optional[TargetCalculationEngine] = None,
    ):
        self.config = config or Phase6Config()
        self.safety_gate = safety_gate or PreOrderSafetyGate(config)
        self.sizing_engine = sizing_engine or PositionSizingEngine(config)
        self.sl_engine = sl_engine or StopLossCalculationEngine(config)
        self.target_engine = target_engine or TargetCalculationEngine(config)

    def prepare_order(
        self,
        entry_price: float,
        option_type: str,
        delta_ce: Optional[float] = None,
        delta_pe: Optional[float] = None,
        gamma_ce: Optional[float] = None,
        gamma_pe: Optional[float] = None,
        current_iv: float = 0.2,
    ) -> dict:
        """
        Prepare complete order with all calculations
        Returns: dict with quantity, SL, target, reasoning
        """

        result = {
            "entry_price": entry_price,
            "option_type": option_type,
            "valid": True,
            "errors": [],
            "calculations": {},
            "delta_entry": delta_ce if option_type == "CE" else delta_pe,
            "gamma_entry": gamma_ce if option_type == "CE" else gamma_pe,
        }

        # Step 1: Calculate SL
        sl_price, sl_method, sl_level = self.sl_engine.calculate_sl_price(
            entry_price=entry_price,
            delta_ce=delta_ce,
            delta_pe=delta_pe,
            gamma_ce=gamma_ce,
            gamma_pe=gamma_pe,
            option_type=option_type,
        )
        result["sl_price"] = sl_price
        result["sl_level"] = sl_level
        result["calculations"]["sl_method"] = sl_method

        # Step 2: Calculate quantity (fixed-risk)
        quantity, actual_risk, sizing_reason = self.sizing_engine.calculate_quantity(
            entry_price=entry_price,
            sl_price=sl_price,
            risk_budget=self.config.fixed_risk_per_trade,
            volatility_factor=1.0 if current_iv < 0.25 else 1.5,
        )
        result["quantity"] = quantity
        result["actual_risk"] = actual_risk
        result["calculations"]["sizing"] = sizing_reason

        # Step 3: Calculate target
        target_price, target_level = self.target_engine.calculate_target_price(
            entry_price=entry_price,
            option_type=option_type,
        )
        result["target_price"] = target_price
        result["target_level"] = target_level

        # Calculate RR ratio
        point_risk = abs(entry_price - sl_price)
        point_reward = abs(target_price - entry_price)
        if point_risk > 0:
            rr_ratio = point_reward / point_risk
            result["risk_reward_ratio"] = rr_ratio

        return result
