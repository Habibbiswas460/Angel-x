"""
Compatibility shim: use the canonical `src.core.risk_manager` implementation.
Keeps all risk limits, veto logic, and Greeks checks centralized.
"""

from src.core.risk_manager import RiskManager, GreeksLimits

__all__ = ["RiskManager", "GreeksLimits"]
