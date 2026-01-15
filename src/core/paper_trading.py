"""
Professional Paper Trading Engine for ANGEL-X
Production-grade simulated trading with realistic market simulation
- Real-time order execution simulation
- Slippage modeling with market impact
- Margin calculation and tracking
- Realistic position management
- Trade journal with all metrics
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple
import json
from pathlib import Path

from config import config
from src.utils.logger import StrategyLogger

logger = StrategyLogger.get_logger(__name__)


class OrderStatus(Enum):
    """Paper trading order statuses"""

    PENDING = "PENDING"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class PositionStatus(Enum):
    """Position statuses"""

    OPEN = "OPEN"
    CLOSED = "CLOSED"
    PARTIALLY_CLOSED = "PARTIALLY_CLOSED"


@dataclass
class PaperOrder:
    """Paper trading order representation"""

    order_id: str
    symbol: str
    action: str  # BUY, SELL
    quantity: int
    price: float
    order_type: str  # MARKET, LIMIT
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: int = 0
    average_price: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    filled_timestamp: Optional[datetime] = None
    rejected_reason: Optional[str] = None
    slippage: float = 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary for logging"""
        return {
            "order_id": self.order_id,
            "symbol": self.symbol,
            "action": self.action,
            "quantity": self.quantity,
            "price": self.price,
            "order_type": self.order_type,
            "status": self.status.value,
            "filled_quantity": self.filled_quantity,
            "average_price": self.average_price,
            "timestamp": self.timestamp.isoformat(),
            "filled_timestamp": self.filled_timestamp.isoformat() if self.filled_timestamp else None,
            "slippage": self.slippage,
            "rejected_reason": self.rejected_reason,
        }


@dataclass
class PaperPosition:
    """Paper trading position representation"""

    symbol: str
    option_type: str  # CE, PE
    strike: int
    quantity: int
    entry_price: float
    entry_time: datetime
    entry_order_id: str
    status: PositionStatus = PositionStatus.OPEN
    current_price: float = 0.0
    last_update: datetime = field(default_factory=datetime.now)
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    exit_order_id: Optional[str] = None

    def calculate_pnl(self, exit_price: Optional[float] = None) -> Tuple[float, float]:
        """Calculate P&L in rupees and percentage"""
        if self.quantity == 0:
            return 0.0, 0.0

        # Use exit_price if provided (for closed trades), otherwise use current_price (for open positions)
        price_to_use = exit_price if exit_price is not None else self.current_price
        price_diff = price_to_use - self.entry_price
        pnl_rupees = price_diff * self.quantity
        pnl_percent = (price_diff / self.entry_price * 100) if self.entry_price != 0 else 0
        return pnl_rupees, pnl_percent

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        pnl_rupees, pnl_percent = self.calculate_pnl()
        return {
            "symbol": self.symbol,
            "option_type": self.option_type,
            "strike": self.strike,
            "quantity": self.quantity,
            "entry_price": self.entry_price,
            "current_price": self.current_price,
            "entry_time": self.entry_time.isoformat(),
            "pnl_rupees": pnl_rupees,
            "pnl_percent": pnl_percent,
            "status": self.status.value,
        }


class PaperTradingEngine:
    """
    Professional Paper Trading Engine
    Simulates real trading with realistic market mechanics
    """

    def __init__(self):
        """Initialize paper trading engine"""
        self.initial_capital = getattr(config, "CAPITAL", 100000)
        self.current_capital = self.initial_capital
        self.utilized_margin = 0.0
        self.available_margin = self.initial_capital

        # Trading data
        self.orders: Dict[str, PaperOrder] = {}
        self.positions: Dict[str, PaperPosition] = {}
        self.closed_trades: List[PaperPosition] = []

        # Order counter
        self._order_counter = 0

        # Statistics
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.gross_pnl = 0.0
        self.net_pnl = 0.0
        self.max_drawdown = 0.0
        self.peak_capital = self.initial_capital

        # Slippage configuration
        self.slippage_percent = getattr(config, "BACKTEST_SLIPPAGE_PERCENT", 0.05) / 100
        self.market_impact_percent = 0.01 / 100  # 0.01% market impact

        # Historical equity
        self.equity_curve = [self.initial_capital]
        self.timestamps = [datetime.now()]

        logger.info(f"PaperTradingEngine initialized | Capital: ₹{self.initial_capital:,.2f}")

    def _generate_order_id(self) -> str:
        """Generate unique paper trading order ID"""
        self._order_counter += 1
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"PAPER_{timestamp}_{self._order_counter:06d}"

    def _calculate_slippage(self, price: float, quantity: int, action: str) -> float:
        """
        Calculate realistic slippage based on market conditions

        Args:
            price: Entry price
            quantity: Order quantity
            action: BUY or SELL

        Returns:
            Slippage amount in rupees
        """
        # Base slippage
        base_slippage = price * self.slippage_percent

        # Market impact (larger orders have more impact)
        impact = price * self.market_impact_percent * (quantity / 75)  # Normalized to 1 lot

        # Direction (BUY = slippage up, SELL = slippage down)
        direction = 1 if action == "BUY" else -1

        total_slippage = direction * (base_slippage + impact)
        return total_slippage

    def place_order(
        self, symbol: str, action: str, quantity: int, price: float, order_type: str = "LIMIT"
    ) -> Tuple[bool, PaperOrder, str]:
        """
        Place a paper trading order

        Args:
            symbol: Option symbol
            action: BUY or SELL
            quantity: Quantity to trade
            price: Order price
            order_type: MARKET or LIMIT

        Returns:
            (success, order, message)
        """
        order_id = self._generate_order_id()

        # Create order
        order = PaperOrder(
            order_id=order_id, symbol=symbol, action=action, quantity=quantity, price=price, order_type=order_type
        )

        # Validate order
        valid, message = self._validate_order(order)
        if not valid:
            order.status = OrderStatus.REJECTED
            order.rejected_reason = message
            self.orders[order_id] = order
            logger.warning(f"Order rejected: {message} | {symbol} {action} {quantity} @ ₹{price}")
            return False, order, message

        # Calculate margin requirement
        margin_required = self._calculate_margin_requirement(symbol, quantity, price)

        # Check margin availability
        if self.available_margin < margin_required:
            order.status = OrderStatus.REJECTED
            order.rejected_reason = (
                f"Insufficient margin. Required: ₹{margin_required:,.2f}, Available: ₹{self.available_margin:,.2f}"
            )
            self.orders[order_id] = order
            logger.error(f"Order rejected - insufficient margin | {order.rejected_reason}")
            return False, order, order.rejected_reason

        # Execute order (simulate immediately for market orders)
        success, message = self._execute_order(order)

        self.orders[order_id] = order

        if success:
            logger.info(
                f"✓ Paper Order Filled | {action} {quantity} {symbol} @ ₹{order.average_price:.2f} | "
                f"Slippage: ₹{abs(order.slippage):.2f}"
            )
            return True, order, message
        else:
            logger.warning(f"Order execution failed: {message}")
            return False, order, message

    def _validate_order(self, order: PaperOrder) -> Tuple[bool, str]:
        """Validate order for compliance"""
        # Validate quantity
        if order.quantity <= 0:
            return False, "Invalid quantity"

        # Validate price
        if order.price <= 0:
            return False, "Invalid price"

        # Check max position size
        max_size = getattr(config, "MAX_POSITION_SIZE", 150)
        if order.quantity > max_size:
            return False, f"Quantity exceeds max position size ({max_size})"

        # Check daily trading limits
        daily_trades = len([p for p in self.closed_trades if self._is_same_day(p.exit_time)])
        max_daily_trades = getattr(config, "MAX_TRADES_PER_DAY", 5)
        if daily_trades >= max_daily_trades:
            return False, f"Daily trade limit reached ({max_daily_trades})"

        return True, "Order valid"

    def _calculate_margin_requirement(self, symbol: str, quantity: int, price: float) -> float:
        """Calculate margin requirement for position"""
        # Typical margin for options: 15-20% of premium value
        margin_percent = 0.15  # 15% margin
        return (price * quantity) * margin_percent

    def _execute_order(self, order: PaperOrder) -> Tuple[bool, str]:
        """Execute paper trading order"""
        # Calculate slippage
        slippage = self._calculate_slippage(order.price, order.quantity, order.action)
        order.slippage = slippage

        # Adjusted price (with slippage)
        adjusted_price = order.price + (slippage / order.quantity)

        # Fill order
        order.filled_quantity = order.quantity
        order.average_price = adjusted_price
        order.status = OrderStatus.FILLED
        order.filled_timestamp = datetime.now()

        # Update margin
        margin = self._calculate_margin_requirement(order.symbol, order.quantity, adjusted_price)
        self.utilized_margin += margin
        self.available_margin -= margin

        # Update or create position
        if order.action == "BUY":
            self._open_long_position(order)
        elif order.action == "SELL":
            self._close_position(order) or self._open_short_position(order)

        # Update equity
        self._update_equity()

        return True, "Order executed successfully"

    def _open_long_position(self, order: PaperOrder):
        """Open a long position"""
        position = PaperPosition(
            symbol=order.symbol,
            option_type=self._extract_option_type(order.symbol),
            strike=self._extract_strike(order.symbol),
            quantity=order.quantity,
            entry_price=order.average_price,
            entry_time=order.filled_timestamp,
            entry_order_id=order.order_id,
            current_price=order.average_price,
        )
        self.positions[order.symbol] = position

    def _close_position(self, sell_order: PaperOrder) -> bool:
        """Close an existing position"""
        symbol = sell_order.symbol
        if symbol not in self.positions:
            return False

        position = self.positions[symbol]

        # Record exit information first
        position.exit_price = sell_order.average_price
        position.exit_time = sell_order.filled_timestamp
        position.exit_order_id = sell_order.order_id

        # Calculate P&L using exit price
        pnl_rupees, pnl_percent = position.calculate_pnl(exit_price=sell_order.average_price)

        position.status = PositionStatus.CLOSED

        # Update statistics
        self.total_trades += 1
        self.gross_pnl += pnl_rupees

        # Track winning/losing trades
        if pnl_rupees > 0:
            self.winning_trades += 1
        elif pnl_rupees < 0:
            self.losing_trades += 1

        # Release margin
        margin = self._calculate_margin_requirement(symbol, position.quantity, position.entry_price)
        self.utilized_margin = max(0, self.utilized_margin - margin)
        self.available_margin = self.current_capital - self.utilized_margin

        # Move to closed trades
        self.closed_trades.append(position)
        del self.positions[symbol]

        logger.info(f"✓ Position Closed | {symbol} | P&L: ₹{pnl_rupees:+.2f} ({pnl_percent:+.2f}%)")

        return True

    def _open_short_position(self, order: PaperOrder):
        """Open a short position (for sell actions without existing long)"""
        position = PaperPosition(
            symbol=order.symbol,
            option_type=self._extract_option_type(order.symbol),
            strike=self._extract_strike(order.symbol),
            quantity=-order.quantity,  # Negative for short
            entry_price=order.average_price,
            entry_time=order.filled_timestamp,
            entry_order_id=order.order_id,
            current_price=order.average_price,
        )
        self.positions[order.symbol] = position

    def _extract_option_type(self, symbol: str) -> str:
        """Extract option type (CE/PE) from symbol"""
        if "CE" in symbol:
            return "CE"
        elif "PE" in symbol:
            return "PE"
        return "UNKNOWN"

    def _extract_strike(self, symbol: str) -> int:
        """Extract strike price from symbol"""
        # Format: NIFTY_25JAN26_19000CE
        parts = symbol.split("_")
        if len(parts) >= 3:
            strike_str = parts[2].replace("CE", "").replace("PE", "")
            try:
                return int(strike_str)
            except:
                pass
        return 0

    def update_position_price(self, symbol: str, current_price: float):
        """Update current price for open position (for real-time P&L tracking)"""
        if symbol in self.positions:
            self.positions[symbol].current_price = current_price
            self.positions[symbol].last_update = datetime.now()
            self._update_equity()

    def _update_equity(self):
        """Update total equity and calculate drawdown"""
        open_pnl = sum(pos.calculate_pnl()[0] for pos in self.positions.values())
        self.current_capital = self.initial_capital + self.gross_pnl + open_pnl
        self.net_pnl = self.gross_pnl + open_pnl

        # Track peak capital for drawdown
        if self.current_capital > self.peak_capital:
            self.peak_capital = self.current_capital

        # Calculate drawdown
        drawdown = max(0, self.peak_capital - self.current_capital)
        self.max_drawdown = max(self.max_drawdown, drawdown)

        # Update equity curve
        self.equity_curve.append(self.current_capital)
        self.timestamps.append(datetime.now())

    def _is_same_day(self, timestamp: Optional[datetime]) -> bool:
        """Check if timestamp is same day as now"""
        if timestamp is None:
            return False
        return timestamp.date() == datetime.now().date()

    def get_statistics(self) -> dict:
        """Get trading statistics"""
        win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0

        return {
            "initial_capital": self.initial_capital,
            "current_capital": self.current_capital,
            "net_pnl": self.net_pnl,
            "gross_pnl": self.gross_pnl,
            "return_percent": (self.net_pnl / self.initial_capital * 100),
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "win_rate": win_rate,
            "max_drawdown": self.max_drawdown,
            "drawdown_percent": (self.max_drawdown / self.peak_capital * 100) if self.peak_capital > 0 else 0,
            "open_positions": len(self.positions),
            "utilized_margin": self.utilized_margin,
            "available_margin": self.available_margin,
        }

    def get_positions(self) -> List[dict]:
        """Get all open positions"""
        return [pos.to_dict() for pos in self.positions.values()]

    def get_order_history(self) -> List[dict]:
        """Get order history"""
        return [order.to_dict() for order in self.orders.values()]

    def get_closed_trades(self) -> List[dict]:
        """Get closed trades"""
        return [trade.to_dict() for trade in self.closed_trades]

    def export_to_json(self, filepath: Optional[str] = None) -> str:
        """Export paper trading session to JSON"""
        if filepath is None:
            filepath = f"paper_trading_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        export_data = {
            "session_timestamp": datetime.now().isoformat(),
            "statistics": self.get_statistics(),
            "orders": self.get_order_history(),
            "open_positions": self.get_positions(),
            "closed_trades": self.get_closed_trades(),
            "equity_curve": self.equity_curve,
        }

        Path(filepath).write_text(json.dumps(export_data, indent=2))
        logger.info(f"Paper trading session exported to {filepath}")
        return filepath

    def reset(self):
        """Reset paper trading engine (for new session)"""
        self.current_capital = self.initial_capital
        self.utilized_margin = 0.0
        self.available_margin = self.initial_capital
        self.orders.clear()
        self.positions.clear()
        self.closed_trades.clear()
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.gross_pnl = 0.0
        self.net_pnl = 0.0
        self.max_drawdown = 0.0
        self.peak_capital = self.initial_capital
        self.equity_curve = [self.initial_capital]
        self.timestamps = [datetime.now()]
        logger.info("Paper trading engine reset")
