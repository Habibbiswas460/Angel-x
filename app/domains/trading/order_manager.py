"""
Compatibility shim: use the canonical `src.core.order_manager` implementation.
This keeps safety gates (TRADING_ENABLED/PAPER_TRADING + RiskManager + quote checks)
in one place. Avoids divergence between app/ and src/ stacks.
"""

from src.core.order_manager import OrderManager, OrderAction, OrderType, ProductType

__all__ = [
    "OrderManager",
    "OrderAction",
    "OrderType",
    "ProductType",
]
