"""
Spread Strategies

Directional and time-based strategies:
- Bull Call Spread
- Bear Put Spread
- Calendar Spread
- Ratio Spread
"""

from typing import List, Dict, Tuple
from .base import MultiLegStrategy, OptionLeg, OptionType, LegDirection
from src.utils.logger import StrategyLogger

logger = StrategyLogger.get_logger(__name__)


class BullCallSpread(MultiLegStrategy):
    """
    Bull Call Spread: Bullish directional strategy

    Structure:
    - Buy 1 Lower Strike Call
    - Sell 1 Higher Strike Call

    Profit: Moderate upward move
    Loss: Price stays flat or drops
    Max Profit: Difference between strikes - Net debit
    Max Loss: Net debit paid

    Best for: Moderately bullish outlook, limited risk
    """

    def __init__(
        self,
        underlying: str = "NIFTY",
        expiry: str = "",
        quantity: int = 1,
        spread_width: int = 100,
        max_loss: float = 3000,
        max_profit: float = 7000,
        width: int = None,
        spread: int = None,
        **kwargs,
    ):
        # Support both width and spread_width parameters
        if width is not None:
            spread_width = width
        if spread is not None:
            spread_width = spread

        super().__init__(
            name="Bull Call Spread",
            underlying=underlying,
            expiry=expiry,
            quantity=quantity,
            max_loss=max_loss,
            max_profit=max_profit,
        )

        self.spread_width = spread_width
        self.long_strike = 0
        self.short_strike = 0
        self.net_debit = 0.0

    def setup(self, spot_price: float, **kwargs) -> List[OptionLeg]:
        """Setup Bull Call Spread"""
        atm_strike = round(spot_price / 100) * 100

        # Long call slightly ITM or ATM
        self.long_strike = int(atm_strike)
        # Short call OTM
        self.short_strike = int(self.long_strike + self.spread_width)

        legs = []

        # Leg 1: Buy Lower Strike Call
        long_premium = kwargs.get("long_call_price", 120.0)
        legs.append(
            OptionLeg(
                strike=self.long_strike,
                option_type=OptionType.CALL,
                direction=LegDirection.BUY,
                quantity=self.quantity,
                entry_price=long_premium,
            )
        )

        # Leg 2: Sell Higher Strike Call
        short_premium = kwargs.get("short_call_price", 60.0)
        legs.append(
            OptionLeg(
                strike=self.short_strike,
                option_type=OptionType.CALL,
                direction=LegDirection.SELL,
                quantity=self.quantity,
                entry_price=short_premium,
            )
        )

        self.net_debit = (long_premium - short_premium) * self.quantity

        logger.info(f"Bull Call Spread: {self.long_strike}/{self.short_strike}\n" f"  Net Debit: ₹{self.net_debit:.2f}")

        return legs

    def validate(self) -> Tuple[bool, str]:
        """Validate Bull Call Spread"""
        if len(self.legs) != 2:
            return False, f"Spread needs 2 legs, got {len(self.legs)}"

        if self.long_strike >= self.short_strike:
            return False, "Long strike must be lower than short strike"

        if self.net_debit <= 0:
            return False, "Net debit must be positive"

        return True, "Valid Bull Call Spread"

    def entry_criteria(self, market_data: Dict) -> Tuple[bool, str]:
        """Entry criteria - moderately bullish"""
        trend = market_data.get("trend", "neutral")

        if trend not in ["bullish", "moderately_bullish"]:
            return False, f"Trend not bullish ({trend})"

        # Check cost vs max reward
        max_profit_potential = self.spread_width * self.quantity
        if self.net_debit > max_profit_potential * 0.7:
            return False, "Spread too expensive (>70% of max profit)"

        return True, "Bullish conditions met"

    def exit_criteria(self, market_data: Dict) -> Tuple[bool, str]:
        """Exit criteria"""
        current_pnl = self.get_total_pnl()
        spot = market_data.get("spot_price", 0)

        # Exit at 75% of max profit
        max_profit = (self.spread_width - self.net_debit / self.quantity) * self.quantity
        if current_pnl >= max_profit * 0.75:
            return True, f"Near max profit (₹{current_pnl:.2f})"

        # Exit if price above short strike (max profit zone)
        if spot >= self.short_strike:
            return True, f"Price at/above short strike"

        # Exit at max loss
        if current_pnl <= -self.net_debit:
            return True, f"Max loss (₹{current_pnl:.2f})"

        # Exit if trend reverses
        if market_data.get("trend") == "bearish" and current_pnl < 0:
            return True, "Trend reversed - cut losses"

        return False, "Hold position"

    def get_max_risk(self) -> float:
        """Max risk = Net debit"""
        return self.net_debit

    def get_max_reward(self) -> float:
        """Max reward = Spread width - Net debit"""
        return (self.spread_width * self.quantity) - self.net_debit

    def get_breakeven_points(self) -> List[float]:
        """Breakeven = Long strike + Net debit per contract"""
        return [self.long_strike + (self.net_debit / self.quantity)]


class BearPutSpread(MultiLegStrategy):
    """
    Bear Put Spread: Bearish directional strategy

    Structure:
    - Buy 1 Higher Strike Put
    - Sell 1 Lower Strike Put

    Profit: Moderate downward move
    Loss: Price stays flat or rises
    Max Profit: Difference between strikes - Net debit
    Max Loss: Net debit paid
    """

    def __init__(
        self,
        underlying: str = "NIFTY",
        expiry: str = "",
        quantity: int = 1,
        spread_width: int = 100,
        max_loss: float = 3000,
        max_profit: float = 7000,
        width: int = None,
        spread: int = None,
        **kwargs,
    ):
        # Support both width and spread_width parameters
        if width is not None:
            spread_width = width
        if spread is not None:
            spread_width = spread

        super().__init__(
            name="Bear Put Spread",
            underlying=underlying,
            expiry=expiry,
            quantity=quantity,
            max_loss=max_loss,
            max_profit=max_profit,
        )

        self.spread_width = spread_width
        self.long_strike = 0
        self.short_strike = 0
        self.net_debit = 0.0

    def setup(self, spot_price: float, **kwargs) -> List[OptionLeg]:
        """Setup Bear Put Spread"""
        atm_strike = round(spot_price / 100) * 100

        # Long put slightly ITM or ATM
        self.long_strike = int(atm_strike)
        # Short put OTM
        self.short_strike = int(self.long_strike - self.spread_width)

        legs = []

        # Leg 1: Buy Higher Strike Put
        long_premium = kwargs.get("long_put_price", 120.0)
        legs.append(
            OptionLeg(
                strike=self.long_strike,
                option_type=OptionType.PUT,
                direction=LegDirection.BUY,
                quantity=self.quantity,
                entry_price=long_premium,
            )
        )

        # Leg 2: Sell Lower Strike Put
        short_premium = kwargs.get("short_put_price", 60.0)
        legs.append(
            OptionLeg(
                strike=self.short_strike,
                option_type=OptionType.PUT,
                direction=LegDirection.SELL,
                quantity=self.quantity,
                entry_price=short_premium,
            )
        )

        self.net_debit = (long_premium - short_premium) * self.quantity

        logger.info(f"Bear Put Spread: {self.long_strike}/{self.short_strike}\n" f"  Net Debit: ₹{self.net_debit:.2f}")

        return legs

    def validate(self) -> Tuple[bool, str]:
        """Validate Bear Put Spread"""
        if len(self.legs) != 2:
            return False, f"Spread needs 2 legs"

        if self.short_strike >= self.long_strike:
            return False, "Short strike must be lower than long strike"

        return True, "Valid Bear Put Spread"

    def entry_criteria(self, market_data: Dict) -> Tuple[bool, str]:
        """Entry criteria - moderately bearish"""
        trend = market_data.get("trend", "neutral")

        if trend not in ["bearish", "moderately_bearish"]:
            return False, f"Trend not bearish"

        return True, "Bearish conditions met"

    def exit_criteria(self, market_data: Dict) -> Tuple[bool, str]:
        """Exit criteria"""
        current_pnl = self.get_total_pnl()
        spot = market_data.get("spot_price", 0)

        max_profit = (self.spread_width - self.net_debit / self.quantity) * self.quantity
        if current_pnl >= max_profit * 0.75:
            return True, f"Near max profit"

        if spot > 0 and spot <= self.short_strike:
            return True, "Price at/below short strike (max profit)"

        return False, "Hold"

    def get_max_risk(self) -> float:
        return self.net_debit

    def get_max_reward(self) -> float:
        return (self.spread_width * self.quantity) - self.net_debit

    def get_breakeven_points(self) -> List[float]:
        return [self.long_strike - (self.net_debit / self.quantity)]


class CalendarSpread(MultiLegStrategy):
    """
    Calendar Spread (Time Spread)

    Structure:
    - Sell Near-term option
    - Buy Far-term option (same strike)

    Profit: Time decay of near-term faster than far-term
    Best for: Neutral outlook, profiting from time decay differential
    """

    def __init__(
        self,
        underlying: str,
        near_expiry: str,
        far_expiry: str,
        quantity: int = 1,
        option_type: OptionType = OptionType.CALL,
    ):
        super().__init__(
            name="Calendar Spread",
            underlying=underlying,
            expiry=near_expiry,  # Use near expiry as primary
            quantity=quantity,
        )

        self.near_expiry = near_expiry
        self.far_expiry = far_expiry
        self.option_type = option_type
        self.strike = 0
        self.net_debit = 0.0

    def setup(self, spot_price: float, **kwargs) -> List[OptionLeg]:
        """Setup Calendar Spread"""
        self.strike = round(spot_price / 100) * 100  # ATM

        legs = []

        # Leg 1: Sell Near-term
        near_premium = kwargs.get("near_premium", 80.0)
        legs.append(
            OptionLeg(
                strike=self.strike,
                option_type=self.option_type,
                direction=LegDirection.SELL,
                quantity=self.quantity,
                entry_price=near_premium,
                expiry=self.near_expiry,
            )
        )

        # Leg 2: Buy Far-term
        far_premium = kwargs.get("far_premium", 120.0)
        legs.append(
            OptionLeg(
                strike=self.strike,
                option_type=self.option_type,
                direction=LegDirection.BUY,
                quantity=self.quantity,
                entry_price=far_premium,
                expiry=self.far_expiry,
            )
        )

        self.net_debit = (far_premium - near_premium) * self.quantity

        logger.info(f"Calendar Spread at {self.strike}, Net Debit: ₹{self.net_debit:.2f}")

        return legs

    def validate(self) -> Tuple[bool, str]:
        return True, "Valid Calendar Spread"

    def entry_criteria(self, market_data: Dict) -> Tuple[bool, str]:
        return True, "Neutral market good for calendar"

    def exit_criteria(self, market_data: Dict) -> Tuple[bool, str]:
        # Exit when near-term expires
        days_to_near_expiry = market_data.get("days_to_expiry", 999)
        if days_to_near_expiry <= 0:
            return True, "Near-term expired"

        current_pnl = self.get_total_pnl()
        if current_pnl >= self.net_debit * 0.5:
            return True, "Good profit on calendar"

        return False, "Hold"

    def get_max_risk(self) -> float:
        return self.net_debit

    def get_max_reward(self) -> float:
        return self.net_debit * 2  # Approximate

    def get_breakeven_points(self) -> List[float]:
        return [self.strike]


class RatioSpread(MultiLegStrategy):
    """
    Ratio Spread: Unequal number of contracts

    Example: Buy 1 ATM Call, Sell 2 OTM Calls

    Profit: Moderate move in expected direction
    Risk: Unlimited if price moves too far
    """

    def __init__(
        self,
        underlying: str,
        expiry: str,
        quantity: int = 1,
        ratio: int = 2,  # Sell 2 for every 1 bought
        option_type: OptionType = OptionType.CALL,
    ):
        super().__init__(
            name=f"{ratio}:1 Ratio Spread",
            underlying=underlying,
            expiry=expiry,
            quantity=quantity,
        )

        self.ratio = ratio
        self.option_type = option_type
        self.long_strike = 0
        self.short_strike = 0

    def setup(self, spot_price: float, **kwargs) -> List[OptionLeg]:
        """Setup Ratio Spread"""
        atm_strike = round(spot_price / 100) * 100

        self.long_strike = atm_strike
        self.short_strike = atm_strike + 100  # OTM

        legs = []

        # Leg 1: Buy ATM
        legs.append(
            OptionLeg(
                strike=self.long_strike,
                option_type=self.option_type,
                direction=LegDirection.BUY,
                quantity=self.quantity,
                entry_price=kwargs.get("long_premium", 100.0),
            )
        )

        # Leg 2: Sell OTM (ratio quantity)
        legs.append(
            OptionLeg(
                strike=self.short_strike,
                option_type=self.option_type,
                direction=LegDirection.SELL,
                quantity=self.quantity * self.ratio,
                entry_price=kwargs.get("short_premium", 50.0),
            )
        )

        logger.info(f"Ratio Spread {self.ratio}:1 setup")

        return legs

    def validate(self) -> Tuple[bool, str]:
        return True, "Valid Ratio Spread"

    def entry_criteria(self, market_data: Dict) -> Tuple[bool, str]:
        return True, "Moderate move expected"

    def exit_criteria(self, market_data: Dict) -> Tuple[bool, str]:
        spot = market_data.get("spot_price", 0)

        # Exit if price moves too far (naked short risk)
        if spot > self.short_strike + 100:
            return True, "Price moved too far - naked risk"

        return False, "Hold"

    def get_max_risk(self) -> float:
        return float("inf")  # Unlimited upside risk

    def get_max_reward(self) -> float:
        return (self.short_strike - self.long_strike) * self.quantity

    def get_breakeven_points(self) -> List[float]:
        # Complex calculation for ratio spreads
        return [self.long_strike, self.short_strike + 50]
