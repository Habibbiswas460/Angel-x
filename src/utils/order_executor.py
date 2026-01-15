"""
PHASE 6 — ATOMIC ORDER PLACEMENT ENGINE

Core principle: Buy order + SL order placed together.
If Buy succeeds but SL fails → EMERGENCY EXIT
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Tuple, Optional, Dict
from src.utils.trade_models import (
    BrokerOrder,
    LinkedOrders,
    OrderType,
    OrderStatus,
    OrderPlacementRequest,
    OrderPlacementResponse,
    Phase6Config,
)


# ============================================================================
# BROKER ORDER SIMULATOR
# ============================================================================


class BrokerInterface:
    """
    Simulated broker interface (actual implementation would use Angel One API)
    For testing: place_order() returns success/failure
    """

    def __init__(self, config: Optional[Phase6Config] = None):
        self.config = config or Phase6Config()
        self.placed_orders: Dict[str, BrokerOrder] = {}
        self.order_counter = 0
        self.last_error: Optional[str] = None

    def place_buy_order(
        self,
        symbol: str,
        option_type: str,
        strike: float,
        quantity: int,
        price: float,
    ) -> Tuple[bool, Optional[str]]:
        """
        Place buy order
        Returns: (success, order_id)
        """

        self.order_counter += 1
        order_id = f"BUY_{self.order_counter}_{datetime.now().timestamp()}"

        order = BrokerOrder(
            order_id=order_id,
            symbol=symbol,
            option_type=option_type,
            strike=strike,
            quantity=quantity,
            order_type=OrderType.BUY,
            price=price,
            status=OrderStatus.PLACED,
        )

        self.placed_orders[order_id] = order
        return True, order_id

    def place_sl_order(
        self,
        symbol: str,
        option_type: str,
        strike: float,
        quantity: int,
        sl_price: float,
        linked_to_order: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Place SL order (linked to buy order)
        Returns: (success, order_id)
        """

        self.order_counter += 1
        order_id = f"SL_{self.order_counter}_{datetime.now().timestamp()}"

        order = BrokerOrder(
            order_id=order_id,
            symbol=symbol,
            option_type=option_type,
            strike=strike,
            quantity=quantity,
            order_type=OrderType.SL,
            price=sl_price,
            status=OrderStatus.PLACED,
        )

        self.placed_orders[order_id] = order
        return True, order_id

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        if order_id in self.placed_orders:
            self.placed_orders[order_id].status = OrderStatus.CANCELLED
            return True
        return False

    def get_order_status(self, order_id: str) -> Optional[OrderStatus]:
        """Get order status"""
        if order_id in self.placed_orders:
            return self.placed_orders[order_id].status
        return None


# ============================================================================
# ATOMIC ORDER PLACEMENT ENGINE
# ============================================================================


class AtomicOrderPlacementEngine:
    """
    Place Buy + SL order atomically (together).
    If one fails after other succeeds → emergency exit triggered
    """

    def __init__(
        self,
        broker: Optional[BrokerInterface] = None,
        config: Optional[Phase6Config] = None,
    ):
        self.broker = broker or BrokerInterface(config)
        self.config = config or Phase6Config()
        self.linked_orders_list: Dict[str, LinkedOrders] = {}
        self.last_error: Optional[str] = None

    def place_atomic_order(
        self,
        symbol: str,
        option_type: str,
        strike: float,
        quantity: int,
        entry_price: float,
        sl_price: float,
        target_price: float,
    ) -> OrderPlacementResponse:
        """
        Place buy order + SL order atomically

        Returns: OrderPlacementResponse with success/failure
        """

        response = OrderPlacementResponse(success=False)

        # Step 1: Place BUY order
        buy_success, buy_order_id = self.broker.place_buy_order(
            symbol=symbol,
            option_type=option_type,
            strike=strike,
            quantity=quantity,
            price=entry_price,
        )

        if not buy_success or buy_order_id is None:
            response.error_message = "Failed to place BUY order"
            self.last_error = response.error_message
            return response

        buy_order = self.broker.placed_orders[buy_order_id]

        # Step 2: Place SL order (linked to buy)
        sl_success, sl_order_id = self.broker.place_sl_order(
            symbol=symbol,
            option_type=option_type,
            strike=strike,
            quantity=quantity,
            sl_price=sl_price,
            linked_to_order=buy_order_id,
        )

        if not sl_success or sl_order_id is None:
            # CRITICAL: Buy succeeded but SL failed
            # Trigger emergency exit
            response.error_message = f"CRITICAL: BUY placed ({buy_order_id}) but SL FAILED. " "EMERGENCY EXIT REQUIRED!"
            self.last_error = response.error_message

            # Cancel the buy order to prevent orphaned position
            self.broker.cancel_order(buy_order_id)

            return response

        sl_order = self.broker.placed_orders[sl_order_id]

        # Step 3: Both orders placed successfully
        linked = LinkedOrders(
            entry_order=buy_order,
            sl_order=sl_order,
            entry_filled=False,
            sl_armed=False,
        )

        self.linked_orders_list[buy_order_id] = linked

        response.success = True
        response.linked_orders = linked
        response.error_message = f"✓ Atomic placement successful: " f"BUY ({buy_order_id}) + SL ({sl_order_id})"

        return response

    def verify_sl_placed(self, order_id: str) -> Tuple[bool, str]:
        """
        Verify that SL order is placed for a buy order
        Returns: (sl_placed, message)
        """

        if order_id not in self.linked_orders_list:
            return False, f"Order {order_id} not found"

        linked = self.linked_orders_list[order_id]

        if linked.sl_order.status != OrderStatus.PLACED:
            return False, f"SL order not placed. Status: {linked.sl_order.status}"

        return True, "SL order verified ✓"

    def simulate_entry_execution(
        self,
        order_id: str,
        filled_price: float,
    ) -> bool:
        """
        Simulate entry order execution (for testing)
        Returns: success
        """

        if order_id not in self.broker.placed_orders:
            return False

        order = self.broker.placed_orders[order_id]
        order.status = OrderStatus.EXECUTED
        order.filled_price = filled_price
        order.filled_quantity = order.quantity

        if order_id in self.linked_orders_list:
            self.linked_orders_list[order_id].entry_filled = True

        return True

    def simulate_sl_execution(
        self,
        order_id: str,
        filled_price: float,
    ) -> bool:
        """
        Simulate SL order execution (for testing)
        Returns: success
        """

        if order_id not in self.broker.placed_orders:
            return False

        order = self.broker.placed_orders[order_id]
        order.status = OrderStatus.EXECUTED
        order.filled_price = filled_price
        order.filled_quantity = order.quantity

        return True


# ============================================================================
# ORPHANED POSITION DETECTOR
# ============================================================================


@dataclass
class OrphanedPositionAlert:
    """Alert for orphaned position (entry filled but no SL)"""

    buy_order_id: str
    entry_price: float
    quantity: int
    filled_time: datetime
    sl_status: str  # WHY SL missing
    risk_exposure: float  # ₹ at risk

    def severity(self) -> str:
        """Severity level"""
        if self.risk_exposure > 1000:
            return "CRITICAL"
        elif self.risk_exposure > 500:
            return "HIGH"
        else:
            return "MEDIUM"


class OrphanedPositionDetector:
    """Detect positions without SL (orphaned positions)"""

    @staticmethod
    def detect_orphaned(linked_orders_list: Dict[str, LinkedOrders]) -> list:
        """
        Detect orphaned positions
        Returns: list of OrphanedPositionAlert
        """

        orphaned = []

        for buy_id, linked in linked_orders_list.items():
            # Check: Entry executed but SL not executed
            if linked.entry_filled and linked.sl_order.status != OrderStatus.EXECUTED:

                risk = calculate_orphaned_risk(
                    entry_price=linked.entry_order.filled_price or 0,
                    quantity=linked.entry_order.quantity,
                )

                alert = OrphanedPositionAlert(
                    buy_order_id=buy_id,
                    entry_price=linked.entry_order.filled_price or 0,
                    quantity=linked.entry_order.quantity,
                    filled_time=linked.entry_order.order_time,
                    sl_status=str(linked.sl_order.status),
                    risk_exposure=risk,
                )

                orphaned.append(alert)

        return orphaned


def calculate_orphaned_risk(entry_price: float, quantity: int) -> float:
    """
    Calculate risk for orphaned position
    Assume worst case: SL at 2% distance
    """
    point_distance = entry_price * 0.02  # 2%
    return point_distance * quantity * 100


# ============================================================================
# EMERGENCY EXIT HANDLER
# ============================================================================


class EmergencyExitHandler:
    """Handle emergency exits (failed SL, manual kill, etc)"""

    def __init__(
        self,
        broker: Optional[BrokerInterface] = None,
    ):
        self.broker = broker or BrokerInterface()
        self.emergency_exits: list = []

    def execute_emergency_exit(
        self,
        buy_order_id: str,
        reason: str,
        current_ltp: float,
        quantity: int,
    ) -> Tuple[bool, str]:
        """
        Execute emergency exit (sell to close)
        Returns: (success, order_id)
        """

        # Note: In real implementation, this would place a SELL order
        # For now, just record it

        exit_record = {
            "buy_order": buy_order_id,
            "reason": reason,
            "exit_price": current_ltp,
            "quantity": quantity,
            "timestamp": datetime.now(),
        }

        self.emergency_exits.append(exit_record)

        return True, f"EXIT_{len(self.emergency_exits)}"

    def get_emergency_exits(self) -> list:
        """Get all emergency exits"""
        return self.emergency_exits
