"""
Base Classes for Multi-leg Option Strategies

Provides foundation for:
- Iron Condor
- Butterfly
- Straddle/Strangle
- Spreads (Bull/Bear/Calendar/Ratio)
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod

from src.utils.logger import StrategyLogger

logger = StrategyLogger.get_logger(__name__)


class OptionType(Enum):
    """Option types"""
    CALL = "CE"
    PUT = "PE"


class LegDirection(Enum):
    """Leg direction in strategy"""
    BUY = "BUY"
    SELL = "SELL"


@dataclass
class OptionLeg:
    """
    Single leg of a multi-leg strategy
    
    Attributes:
        strike: Strike price
        option_type: CE or PE
        direction: BUY or SELL
        quantity: Number of contracts
        entry_price: Entry price (premium)
        current_price: Current market price
        token: Instrument token
        expiry: Expiry date
    """
    strike: int
    option_type: OptionType
    direction: LegDirection
    quantity: int
    entry_price: float = 0.0
    current_price: float = 0.0
    token: str = ""
    expiry: str = ""
    
    # Greeks
    delta: float = 0.0
    gamma: float = 0.0
    theta: float = 0.0
    vega: float = 0.0
    iv: float = 0.0
    
    def get_pnl(self) -> float:
        """Calculate P&L for this leg"""
        if self.entry_price == 0:
            return 0.0
        
        price_diff = self.current_price - self.entry_price
        
        if self.direction == LegDirection.BUY:
            return price_diff * self.quantity
        else:  # SELL
            return -price_diff * self.quantity
    
    def get_notional_value(self) -> float:
        """Get current notional value"""
        return self.current_price * self.quantity
    
    def __str__(self) -> str:
        return (
            f"{self.direction.value} {self.quantity}x "
            f"{self.strike}{self.option_type.value} @ {self.entry_price:.2f}"
        )


class MultiLegStrategy(ABC):
    """
    Base class for multi-leg option strategies
    
    All strategies must implement:
    - setup(): Define legs
    - validate(): Check if setup is valid
    - entry_criteria(): When to enter
    - exit_criteria(): When to exit
    - adjust(): How to adjust position
    """
    
    def __init__(
        self,
        name: str,
        underlying: str,
        expiry: str,
        quantity: int = 1,
        max_loss: float = 5000,
        max_profit: float = 10000,
    ):
        """
        Initialize multi-leg strategy
        
        Args:
            name: Strategy name
            underlying: Underlying symbol (NIFTY, BANKNIFTY)
            expiry: Expiry date
            quantity: Lot size
            max_loss: Maximum acceptable loss
            max_profit: Target profit
        """
        self.name = name
        self.underlying = underlying
        self.expiry = expiry
        self.quantity = quantity
        self.max_loss = max_loss
        self.max_profit = max_profit
        
        # Legs
        self.legs: List[OptionLeg] = []
        
        # State
        self.is_active = False
        self.entry_time: Optional[datetime] = None
        self.exit_time: Optional[datetime] = None
        
        # P&L tracking
        self.realized_pnl = 0.0
        self.max_profit_seen = 0.0
        self.max_loss_seen = 0.0
        
        # Greeks aggregation
        self.net_delta = 0.0
        self.net_gamma = 0.0
        self.net_theta = 0.0
        self.net_vega = 0.0
        
        logger.info(f"{name} strategy initialized: {underlying} {expiry}")
    
    @abstractmethod
    def setup(self, spot_price: float, **kwargs) -> List[OptionLeg]:
        """
        Setup strategy legs
        
        Args:
            spot_price: Current spot price
            **kwargs: Strategy-specific parameters
            
        Returns:
            List of option legs
        """
        pass
    
    @abstractmethod
    def validate(self) -> Tuple[bool, str]:
        """
        Validate strategy setup
        
        Returns:
            (is_valid, error_message)
        """
        pass
    
    @abstractmethod
    def entry_criteria(self, market_data: Dict) -> Tuple[bool, str]:
        """
        Check if entry conditions are met
        
        Args:
            market_data: Current market data
            
        Returns:
            (should_enter, reason)
        """
        pass
    
    @abstractmethod
    def exit_criteria(self, market_data: Dict) -> Tuple[bool, str]:
        """
        Check if exit conditions are met
        
        Args:
            market_data: Current market data
            
        Returns:
            (should_exit, reason)
        """
        pass
    
    def enter(self, spot_price: float, **kwargs) -> bool:
        """
        Enter the strategy
        
        Args:
            spot_price: Current spot price
            **kwargs: Strategy-specific parameters
            
        Returns:
            True if entry successful
        """
        try:
            # Setup legs
            self.legs = self.setup(spot_price, **kwargs)
            
            # Validate
            is_valid, error_msg = self.validate()
            if not is_valid:
                logger.error(f"Strategy validation failed: {error_msg}")
                return False
            
            # Mark as active
            self.is_active = True
            self.entry_time = datetime.now()
            
            logger.info(f"✅ Entered {self.name} with {len(self.legs)} legs")
            for leg in self.legs:
                logger.info(f"  {leg}")
            
            return True
            
        except Exception as e:
            logger.error(f"Entry error: {e}")
            return False
    
    def exit(self, reason: str = "Manual") -> bool:
        """
        Exit the strategy
        
        Args:
            reason: Reason for exit
            
        Returns:
            True if exit successful
        """
        try:
            if not self.is_active:
                logger.warning("Strategy not active")
                return False
            
            # Calculate final P&L
            self.realized_pnl = self.get_total_pnl()
            
            # Mark as inactive
            self.is_active = False
            self.exit_time = datetime.now()
            
            duration = (self.exit_time - self.entry_time).total_seconds() / 60
            
            logger.info(
                f"🚪 Exited {self.name}: {reason}\n"
                f"   P&L: ₹{self.realized_pnl:.2f}\n"
                f"   Duration: {duration:.1f} minutes"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Exit error: {e}")
            return False
    
    def update_prices(self, price_data: Dict[str, float]):
        """
        Update leg prices from market data
        
        Args:
            price_data: {token: current_price}
        """
        for leg in self.legs:
            if leg.token in price_data:
                leg.current_price = price_data[leg.token]
        
        # Update Greeks aggregation
        self._update_greeks()
    
    def update_greeks(self, greeks_data: Dict[str, Dict]):
        """
        Update Greeks for all legs
        
        Args:
            greeks_data: {token: {delta, gamma, theta, vega, iv}}
        """
        for leg in self.legs:
            if leg.token in greeks_data:
                greeks = greeks_data[leg.token]
                leg.delta = greeks.get('delta', 0.0)
                leg.gamma = greeks.get('gamma', 0.0)
                leg.theta = greeks.get('theta', 0.0)
                leg.vega = greeks.get('vega', 0.0)
                leg.iv = greeks.get('iv', 0.0)
        
        self._update_greeks()
    
    def _update_greeks(self):
        """Aggregate Greeks across all legs"""
        self.net_delta = 0.0
        self.net_gamma = 0.0
        self.net_theta = 0.0
        self.net_vega = 0.0
        
        for leg in self.legs:
            multiplier = 1 if leg.direction == LegDirection.BUY else -1
            
            self.net_delta += leg.delta * leg.quantity * multiplier
            self.net_gamma += leg.gamma * leg.quantity * multiplier
            self.net_theta += leg.theta * leg.quantity * multiplier
            self.net_vega += leg.vega * leg.quantity * multiplier
    
    def get_total_pnl(self) -> float:
        """Get total P&L across all legs"""
        return sum(leg.get_pnl() for leg in self.legs)
    
    def get_max_risk(self) -> float:
        """Calculate maximum risk (theoretical)"""
        # To be overridden by specific strategies
        return self.max_loss
    
    def get_max_reward(self) -> float:
        """Calculate maximum reward (theoretical)"""
        # To be overridden by specific strategies
        return self.max_profit
    
    def get_breakeven_points(self) -> List[float]:
        """Calculate breakeven points"""
        # To be overridden by specific strategies
        return []
    
    def get_summary(self) -> Dict:
        """Get strategy summary"""
        return {
            'name': self.name,
            'underlying': self.underlying,
            'expiry': self.expiry,
            'is_active': self.is_active,
            'legs_count': len(self.legs),
            'total_pnl': self.get_total_pnl(),
            'realized_pnl': self.realized_pnl,
            'net_delta': self.net_delta,
            'net_gamma': self.net_gamma,
            'net_theta': self.net_theta,
            'net_vega': self.net_vega,
            'max_risk': self.get_max_risk(),
            'max_reward': self.get_max_reward(),
            'entry_time': self.entry_time,
            'exit_time': self.exit_time,
        }
    
    def get_leg_details(self) -> List[Dict]:
        """Get details of all legs"""
        return [
            {
                'strike': leg.strike,
                'option_type': leg.option_type.value,
                'direction': leg.direction.value,
                'quantity': leg.quantity,
                'entry_price': leg.entry_price,
                'current_price': leg.current_price,
                'pnl': leg.get_pnl(),
                'delta': leg.delta,
                'gamma': leg.gamma,
                'theta': leg.theta,
                'vega': leg.vega,
                'iv': leg.iv,
            }
            for leg in self.legs
        ]
    
    def check_adjustment_needed(self) -> Tuple[bool, str]:
        """
        Check if position needs adjustment
        
        Returns:
            (needs_adjustment, reason)
        """
        # Check Greeks thresholds
        if abs(self.net_delta) > 50:
            return True, f"High delta exposure: {self.net_delta:.2f}"
        
        if abs(self.net_gamma) > 5:
            return True, f"High gamma exposure: {self.net_gamma:.4f}"
        
        # Check P&L thresholds
        current_pnl = self.get_total_pnl()
        
        if current_pnl <= -self.max_loss:
            return True, f"Max loss reached: ₹{current_pnl:.2f}"
        
        if current_pnl >= self.max_profit:
            return True, f"Target profit reached: ₹{current_pnl:.2f}"
        
        return False, "No adjustment needed"
    
    def adjust(self, adjustment_type: str, **kwargs) -> bool:
        """
        Adjust strategy position
        
        Args:
            adjustment_type: Type of adjustment (add_leg, remove_leg, roll, etc.)
            **kwargs: Adjustment parameters
            
        Returns:
            True if adjustment successful
        """
        # To be implemented by specific strategies
        logger.warning(f"Adjustment not implemented for {self.name}")
        return False
    
    def __str__(self) -> str:
        status = "ACTIVE" if self.is_active else "INACTIVE"
        pnl = self.get_total_pnl()
        return (
            f"{self.name} [{status}] | "
            f"Legs: {len(self.legs)} | "
            f"P&L: ₹{pnl:.2f} | "
            f"Δ: {self.net_delta:.2f}"
        )
