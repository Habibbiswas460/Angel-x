"""
Straddle and Strangle Strategies

Volatility-based strategies that profit from large price movements
"""

from typing import List, Dict, Tuple
from .base import MultiLegStrategy, OptionLeg, OptionType, LegDirection, Leg
from src.utils.logger import StrategyLogger

logger = StrategyLogger.get_logger(__name__)


class StraddleStrategy(MultiLegStrategy):
    """
    Long Straddle: Buy ATM Call + Buy ATM Put

    Structure:
    - Buy 1 ATM Call
    - Buy 1 ATM Put

    Profit: Large move in either direction
    Loss: Price stays near ATM strike (time decay)
    Max Profit: Unlimited (upside), Strike - Total Premium (downside)
    Max Loss: Total premium paid

    Best for: High volatility expected (earnings, events)
    """

    def __init__(
        self,
        underlying: str,
        expiry: str,
        quantity: int = 1,
        max_loss: float = 5000,
        max_profit: float = 15000,
    ):
        super().__init__(
            name="Long Straddle",
            underlying=underlying,
            expiry=expiry,
            quantity=quantity,
            max_loss=max_loss,
            max_profit=max_profit,
        )

        self.atm_strike = 0
        self.total_premium_paid = 0.0

    def setup(self, spot_price: float, **kwargs) -> List[OptionLeg]:
        """Setup Straddle legs"""
        # ATM strike (nearest to spot)
        self.atm_strike = round(spot_price / 100) * 100

        legs = []

        # Leg 1: Buy ATM Call
        call_premium = kwargs.get("call_price", 100.0)
        legs.append(
            OptionLeg(
                strike=self.atm_strike,
                option_type=OptionType.CALL,
                direction=LegDirection.BUY,
                quantity=self.quantity,
                entry_price=call_premium,
            )
        )

        # Leg 2: Buy ATM Put
        put_premium = kwargs.get("put_price", 100.0)
        legs.append(
            OptionLeg(
                strike=self.atm_strike,
                option_type=OptionType.PUT,
                direction=LegDirection.BUY,
                quantity=self.quantity,
                entry_price=put_premium,
            )
        )

        self.total_premium_paid = (call_premium + put_premium) * self.quantity

        logger.info(f"Straddle setup at strike {self.atm_strike}\n" f"  Total Premium: ₹{self.total_premium_paid:.2f}")

        return legs

    def validate(self) -> Tuple[bool, str]:
        """Validate Straddle"""
        if len(self.legs) != 2:
            return False, f"Straddle needs 2 legs, got {len(self.legs)}"

        # Both legs should be at same strike
        if self.legs[0].strike != self.legs[1].strike:
            return False, "Straddle legs must have same strike"

        # Both should be BUY
        if any(leg.direction != LegDirection.BUY for leg in self.legs):
            return False, "Straddle requires buying both legs"

        return True, "Valid Straddle"

    def entry_criteria(self, market_data: Dict) -> Tuple[bool, str]:
        """
        Entry criteria for Straddle

        Good conditions:
        - High IV expected (before earnings/events)
        - Low current IV (buy cheap options)
        - Significant catalyst expected
        """
        iv = market_data.get("iv", 0)
        iv_rank = market_data.get("iv_rank", 50)  # IV percentile

        # Enter when IV is relatively low but spike expected
        if iv > 30:
            return False, f"IV too high ({iv:.1f}%) - options expensive"

        # Check for catalyst
        has_event = market_data.get("upcoming_event", False)
        if not has_event:
            logger.warning("No catalyst detected - consider waiting")

        # Check premium cost vs account size
        if self.total_premium_paid > self.max_loss:
            return False, f"Premium (₹{self.total_premium_paid:.2f}) exceeds max loss"

        return True, "Favorable for Straddle entry"

    def exit_criteria(self, market_data: Dict) -> Tuple[bool, str]:
        """Exit criteria for Straddle"""
        current_pnl = self.get_total_pnl()
        spot = market_data.get("spot_price", 0)

        # Exit at profit target
        if current_pnl >= self.max_profit:
            return True, f"Profit target reached (₹{current_pnl:.2f})"

        # Exit at max loss (total premium lost)
        if current_pnl <= -self.total_premium_paid:
            return True, f"Max loss reached (₹{current_pnl:.2f})"

        # Exit if significant move captured
        if spot > 0:
            move_pct = abs((spot - self.atm_strike) / self.atm_strike) * 100
            if move_pct > 5 and current_pnl > 0:
                return True, f"Large move captured ({move_pct:.1f}%)"

        # Exit near expiry if losing
        days_to_expiry = market_data.get("days_to_expiry", 999)
        if days_to_expiry <= 2 and current_pnl < -self.total_premium_paid * 0.5:
            return True, "Near expiry with significant loss"

        # Exit after event if IV crushed
        iv = market_data.get("iv", 0)
        if iv < 10 and current_pnl < 0:
            return True, f"IV crushed ({iv:.1f}%) - cut losses"

        return False, "Hold position"

    def get_max_risk(self) -> float:
        """Max risk = Total premium paid"""
        return self.total_premium_paid

    def get_max_reward(self) -> float:
        """Max reward = Unlimited (theoretically)"""
        return float("inf")  # Or use max_profit parameter

    def get_breakeven_points(self) -> List[float]:
        """Calculate breakeven points"""
        premium_per_leg = self.total_premium_paid / self.quantity
        return [
            self.atm_strike - premium_per_leg,  # Lower breakeven
            self.atm_strike + premium_per_leg,  # Upper breakeven
        ]


class StrangleStrategy(MultiLegStrategy):
    """
    Long Strangle: Buy OTM Call + Buy OTM Put

    Structure:
    - Buy 1 OTM Call
    - Buy 1 OTM Put

    Similar to Straddle but:
    - Lower cost (OTM options cheaper)
    - Need larger move to profit
    - Lower risk, lower reward

    Best for: Expecting big move but want lower cost
    """

    def __init__(
        self,
        underlying: str,
        expiry: str,
        quantity: int = 1,
        otm_distance: int = 100,  # Distance from ATM
        max_loss: float = 4000,
        max_profit: float = 12000,
    ):
        super().__init__(
            name="Long Strangle",
            underlying=underlying,
            expiry=expiry,
            quantity=quantity,
            max_loss=max_loss,
            max_profit=max_profit,
        )

        self.otm_distance = otm_distance
        self.call_strike = 0
        self.put_strike = 0
        self.total_premium_paid = 0.0

    def setup(self, spot_price: float, **kwargs) -> List[OptionLeg]:
        """Setup Strangle legs"""
        atm_strike = round(spot_price / 100) * 100

        # OTM strikes
        self.put_strike = int(atm_strike - self.otm_distance)
        self.call_strike = int(atm_strike + self.otm_distance)

        legs = []

        # Leg 1: Buy OTM Call
        call_premium = kwargs.get("call_price", 60.0)
        legs.append(
            OptionLeg(
                strike=self.call_strike,
                option_type=OptionType.CALL,
                direction=LegDirection.BUY,
                quantity=self.quantity,
                entry_price=call_premium,
            )
        )

        # Leg 2: Buy OTM Put
        put_premium = kwargs.get("put_price", 60.0)
        legs.append(
            OptionLeg(
                strike=self.put_strike,
                option_type=OptionType.PUT,
                direction=LegDirection.BUY,
                quantity=self.quantity,
                entry_price=put_premium,
            )
        )

        self.total_premium_paid = (call_premium + put_premium) * self.quantity

        logger.info(
            f"Strangle setup:\n"
            f"  Put Strike: {self.put_strike}\n"
            f"  Call Strike: {self.call_strike}\n"
            f"  Total Premium: ₹{self.total_premium_paid:.2f}"
        )

        return legs

    def validate(self) -> Tuple[bool, str]:
        """Validate Strangle"""
        if len(self.legs) != 2:
            return False, f"Strangle needs 2 legs, got {len(self.legs)}"

        # Put strike should be lower than call strike
        if self.put_strike >= self.call_strike:
            return False, "Put strike must be lower than call strike"

        # Both should be BUY
        if any(leg.direction != LegDirection.BUY for leg in self.legs):
            return False, "Strangle requires buying both legs"

        return True, "Valid Strangle"

    def entry_criteria(self, market_data: Dict) -> Tuple[bool, str]:
        """Entry criteria for Strangle (similar to Straddle)"""
        iv = market_data.get("iv", 0)

        if iv > 35:
            return False, f"IV too high ({iv:.1f}%)"

        if self.total_premium_paid > self.max_loss:
            return False, f"Premium exceeds max loss"

        return True, "Favorable for Strangle entry"

    def exit_criteria(self, market_data: Dict) -> Tuple[bool, str]:
        """Exit criteria for Strangle"""
        current_pnl = self.get_total_pnl()
        spot = market_data.get("spot_price", 0)

        # Exit at profit target
        if current_pnl >= self.max_profit:
            return True, f"Profit target (₹{current_pnl:.2f})"

        # Exit at max loss
        if current_pnl <= -self.total_premium_paid:
            return True, f"Max loss (₹{current_pnl:.2f})"

        # Exit if price beyond strike + profitable
        if spot > 0:
            if (spot > self.call_strike or spot < self.put_strike) and current_pnl > 0:
                return True, f"Price beyond strike with profit"

        # Exit near expiry
        days_to_expiry = market_data.get("days_to_expiry", 999)
        if days_to_expiry <= 3 and current_pnl < 0:
            return True, "Near expiry - cut losses"

        return False, "Hold position"

    def get_max_risk(self) -> float:
        """Max risk = Total premium paid"""
        return self.total_premium_paid

    def get_max_reward(self) -> float:
        """Max reward = Unlimited"""
        return float("inf")

    def get_breakeven_points(self) -> List[float]:
        """Calculate breakeven points"""
        premium_per_leg = self.total_premium_paid / self.quantity
        return [
            self.put_strike - premium_per_leg,  # Lower breakeven
            self.call_strike + premium_per_leg,  # Upper breakeven
        ]


# Minimal straddle variants expected by tests
class ShortStraddle(MultiLegStrategy):
    def __init__(self, spread: int = 0, **kwargs):
        super().__init__(name="Short Straddle")
        self.spread = spread if spread > 0 else 50

    def build_legs(self, spot: float) -> List[Leg]:
        strike = round(spot / self.spread) * self.spread
        return [
            Leg(
                instrument=f"{self.underlying}{self.expiry}{strike}CE",
                strike=strike,
                kind="CALL",
                expiry=self.expiry,
                qty=self.quantity,
                entry_price=0.0,
                side="SELL",
            ),
            Leg(
                instrument=f"{self.underlying}{self.expiry}{strike}PE",
                strike=strike,
                kind="PUT",
                expiry=self.expiry,
                qty=self.quantity,
                entry_price=0.0,
                side="SELL",
            ),
        ]


class LongStraddle(MultiLegStrategy):
    def __init__(self, spread: int = 0, **kwargs):
        super().__init__(name="Long Straddle")
        self.spread = spread if spread > 0 else 50

    def build_legs(self, spot: float) -> List[Leg]:
        strike = round(spot / self.spread) * self.spread
        return [
            Leg(
                instrument=f"{self.underlying}{self.expiry}{strike}CE",
                strike=strike,
                kind="CALL",
                expiry=self.expiry,
                qty=self.quantity,
                entry_price=0.0,
                side="BUY",
            ),
            Leg(
                instrument=f"{self.underlying}{self.expiry}{strike}PE",
                strike=strike,
                kind="PUT",
                expiry=self.expiry,
                qty=self.quantity,
                entry_price=0.0,
                side="BUY",
            ),
        ]
