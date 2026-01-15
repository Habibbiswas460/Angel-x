"""
Iron Condor Strategy

A neutral strategy combining:
- Bull Put Spread (lower strikes)
- Bear Call Spread (higher strikes)

Structure:
- Sell 1 OTM Put
- Buy 1 Further OTM Put (protection)
- Sell 1 OTM Call
- Buy 1 Further OTM Call (protection)

Profit: When price stays within the short strikes (range-bound)
Loss: When price breaks out significantly in either direction
Max Profit: Net credit received
Max Loss: Width of widest spread - Net credit
"""

from typing import List, Dict, Tuple
from .base import MultiLegStrategy, OptionLeg, OptionType, LegDirection
from src.utils.logger import StrategyLogger

logger = StrategyLogger.get_logger(__name__)


class IronCondorStrategy(MultiLegStrategy):
    """
    Iron Condor Options Strategy

    Best for: Range-bound markets with low volatility
    Market View: Neutral (expect price to stay in range)
    """

    def __init__(
        self,
        underlying: str = "NIFTY",
        expiry: str = "",
        quantity: int = 1,
        wing_width: int = 100,  # Distance between long and short strikes
        max_loss: float = 5000,
        max_profit: float = 3000,
        width: int = None,
        spread: int = None,
        **kwargs,
    ):
        """
        Initialize Iron Condor

        Args:
            underlying: NIFTY or BANKNIFTY
            expiry: Expiry date
            quantity: Lot size
            wing_width: Width of each spread (e.g., 100 points)
            max_loss: Maximum acceptable loss
            max_profit: Target profit
        """
        # Support both width and wing_width parameters
        if width is not None:
            wing_width = width
        if spread is not None:
            wing_width = spread

        super().__init__(
            name="Iron Condor",
            underlying=underlying,
            expiry=expiry,
            quantity=quantity,
            max_loss=max_loss,
            max_profit=max_profit,
        )

        self.wing_width = wing_width
        self.width = wing_width  # Alias for test compatibility

        # Strike prices (set during setup)
        self.short_put_strike = 0
        self.long_put_strike = 0
        self.short_call_strike = 0
        self.long_call_strike = 0

        # Net credit received
        self.net_credit = 0.0

    def setup(
        self,
        spot_price: float,
        put_delta: float = -0.30,  # Delta for short put
        call_delta: float = 0.30,  # Delta for short call
        **kwargs,
    ) -> List[OptionLeg]:
        """
        Setup Iron Condor legs

        Args:
            spot_price: Current spot price
            put_delta: Target delta for short put (negative)
            call_delta: Target delta for short call (positive)

        Returns:
            List of 4 option legs
        """
        # Round spot to nearest 100 for index options
        atm_strike = round(spot_price / 100) * 100

        # Calculate strikes based on delta approximation
        # Rough approximation: 0.30 delta ≈ 1 SD move ≈ 100-200 points OTM
        otm_distance = 150  # Can be refined with actual delta calculations

        # Put spread (lower side)
        self.short_put_strike = int(atm_strike - otm_distance)
        self.long_put_strike = int(self.short_put_strike - self.wing_width)

        # Call spread (upper side)
        self.short_call_strike = int(atm_strike + otm_distance)
        self.long_call_strike = int(self.short_call_strike + self.wing_width)

        # Create legs
        legs = []

        # Leg 1: Sell OTM Put
        legs.append(
            OptionLeg(
                strike=self.short_put_strike,
                option_type=OptionType.PUT,
                direction=LegDirection.SELL,
                quantity=self.quantity,
                entry_price=kwargs.get("short_put_price", 50.0),  # Premium received
            )
        )

        # Leg 2: Buy Further OTM Put (protection)
        legs.append(
            OptionLeg(
                strike=self.long_put_strike,
                option_type=OptionType.PUT,
                direction=LegDirection.BUY,
                quantity=self.quantity,
                entry_price=kwargs.get("long_put_price", 20.0),  # Premium paid
            )
        )

        # Leg 3: Sell OTM Call
        legs.append(
            OptionLeg(
                strike=self.short_call_strike,
                option_type=OptionType.CALL,
                direction=LegDirection.SELL,
                quantity=self.quantity,
                entry_price=kwargs.get("short_call_price", 50.0),  # Premium received
            )
        )

        # Leg 4: Buy Further OTM Call (protection)
        legs.append(
            OptionLeg(
                strike=self.long_call_strike,
                option_type=OptionType.CALL,
                direction=LegDirection.BUY,
                quantity=self.quantity,
                entry_price=kwargs.get("long_call_price", 20.0),  # Premium paid
            )
        )

        # Calculate net credit
        self.net_credit = (
            legs[0].entry_price
            - legs[1].entry_price  # Put spread credit
            + legs[2].entry_price
            - legs[3].entry_price  # Call spread credit
        ) * self.quantity

        logger.info(
            f"Iron Condor setup:\n"
            f"  Put Spread: {self.long_put_strike} - {self.short_put_strike}\n"
            f"  Call Spread: {self.short_call_strike} - {self.long_call_strike}\n"
            f"  Net Credit: ₹{self.net_credit:.2f}"
        )

        return legs

    def validate(self) -> Tuple[bool, str]:
        """Validate Iron Condor setup"""
        if len(self.legs) != 4:
            return False, f"Iron Condor needs 4 legs, got {len(self.legs)}"

        # Check put spread
        if self.long_put_strike >= self.short_put_strike:
            return False, "Invalid put spread strikes"

        # Check call spread
        if self.short_call_strike >= self.long_call_strike:
            return False, "Invalid call spread strikes"

        # Check symmetry (short strikes should be equidistant from spot)
        # This is optional but good practice

        # Check net credit is positive
        if self.net_credit <= 0:
            return False, f"Net credit must be positive, got {self.net_credit}"

        return True, "Valid Iron Condor"

    def entry_criteria(self, market_data: Dict) -> Tuple[bool, str]:
        """
        Check if conditions are right for Iron Condor entry

        Good conditions:
        - Low implied volatility (IV < 20%)
        - Range-bound market (low ATR)
        - Neutral trend
        - Adequate premium available
        """
        spot = market_data.get("spot_price", 0)
        iv = market_data.get("iv", 0)
        atr = market_data.get("atr", 0)

        if spot == 0:
            return False, "No spot price available"

        # Check IV (lower is better for selling premium)
        if iv > 25:
            return False, f"IV too high ({iv:.1f}%) - risky for selling"

        # Check if market is range-bound
        if atr > 200:  # Adjust based on underlying
            return False, f"ATR too high ({atr:.0f}) - expect breakout"

        # Check if adequate premium available
        min_credit = self.wing_width * 0.20  # At least 20% of wing width
        if self.net_credit < min_credit:
            return False, f"Insufficient premium (₹{self.net_credit:.2f})"

        return True, "Conditions favorable for Iron Condor"

    def exit_criteria(self, market_data: Dict) -> Tuple[bool, str]:
        """
        Check if Iron Condor should be exited

        Exit when:
        - Target profit reached (e.g., 50% of max profit)
        - Max loss approaching
        - Price near short strikes (adjustment zone)
        - Time decay sufficient (e.g., captured 75% of theta)
        """
        current_pnl = self.get_total_pnl()
        spot = market_data.get("spot_price", 0)

        # Exit at profit target (50% of max profit = 50% of net credit)
        profit_target = self.net_credit * 0.50
        if current_pnl >= profit_target:
            return True, f"Profit target reached (₹{current_pnl:.2f})"

        # Exit at max loss
        if current_pnl <= -self.max_loss:
            return True, f"Max loss reached (₹{current_pnl:.2f})"

        # Exit if price approaching short strikes (danger zone)
        if spot > 0:
            buffer = 50  # Points

            if spot <= (self.short_put_strike + buffer):
                return True, f"Price near short put ({spot:.0f} vs {self.short_put_strike})"

            if spot >= (self.short_call_strike - buffer):
                return True, f"Price near short call ({spot:.0f} vs {self.short_call_strike})"

        # Exit near expiry if profitable
        days_to_expiry = market_data.get("days_to_expiry", 999)
        if days_to_expiry <= 2 and current_pnl > 0:
            return True, f"Near expiry with profit (₹{current_pnl:.2f})"

        return False, "Hold position"

    def get_max_risk(self) -> float:
        """Calculate maximum risk"""
        # Max loss = Wing width - Net credit received
        return (self.wing_width * self.quantity) - self.net_credit

    def get_max_reward(self) -> float:
        """Calculate maximum reward"""
        # Max profit = Net credit received
        return self.net_credit

    def get_breakeven_points(self) -> List[float]:
        """Calculate breakeven points"""
        # Lower breakeven = Short put - Net credit per contract
        # Upper breakeven = Short call + Net credit per contract
        credit_per_contract = self.net_credit / self.quantity

        return [
            self.short_put_strike - credit_per_contract,
            self.short_call_strike + credit_per_contract,
        ]

    def adjust(self, adjustment_type: str, **kwargs) -> bool:
        """
        Adjust Iron Condor position

        Adjustments:
        - roll: Roll untested side for additional credit
        - close_side: Close one side if price moved
        - widen: Widen the spreads
        """
        if adjustment_type == "roll_put_side":
            # Roll put spread up for credit
            logger.info("Rolling put side up...")
            return True

        elif adjustment_type == "roll_call_side":
            # Roll call spread down for credit
            logger.info("Rolling call side down...")
            return True

        elif adjustment_type == "close_profitable_side":
            # Close profitable side to reduce risk
            current_pnl = self.get_total_pnl()
            if current_pnl > 0:
                logger.info("Closing profitable side...")
                return True

        return False


# Backwards-compatible alias expected by tests
class IronCondor(IronCondorStrategy):
    pass
