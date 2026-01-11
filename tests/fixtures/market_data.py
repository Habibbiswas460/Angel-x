"""
Test fixtures for ANGEL-X
"""

import pytest
from dataclasses import dataclass
from datetime import datetime


@dataclass
class MockTick:
    """Mock market tick data"""
    timestamp: datetime
    ltp: float
    bid: float
    ask: float
    volume: int
    oi: int
    
    @staticmethod
    def sample(ltp=100.0, bid=99.5, ask=100.5, volume=1000, oi=500000):
        """Create a sample tick"""
        return MockTick(
            timestamp=datetime.now(),
            ltp=ltp,
            bid=bid,
            ask=ask,
            volume=volume,
            oi=oi
        )


@dataclass
class MockGreeks:
    """Mock Greeks data"""
    delta: float
    gamma: float
    theta: float
    vega: float
    iv: float
    
    @staticmethod
    def sample(delta=0.50, gamma=0.003, theta=-0.02, vega=0.05, iv=25.0):
        """Create sample Greeks"""
        return MockGreeks(
            delta=delta,
            gamma=gamma,
            theta=theta,
            vega=vega,
            iv=iv
        )


@dataclass
class MockPosition:
    """Mock trading position"""
    symbol: str
    option_type: str
    strike: int
    entry_price: float
    entry_delta: float
    current_price: float
    quantity: int
    entry_time: datetime
    
    def unrealized_pnl(self) -> float:
        """Calculate unrealized P&L"""
        return (self.current_price - self.entry_price) * self.quantity


# Pytest fixtures
@pytest.fixture
def sample_tick():
    """Provide sample tick data"""
    return MockTick.sample()


@pytest.fixture
def sample_greeks():
    """Provide sample Greeks"""
    return MockGreeks.sample()


@pytest.fixture
def sample_position():
    """Provide sample position"""
    return MockPosition(
        symbol="NIFTY_25JAN26_19000CE",
        option_type="CE",
        strike=19000,
        entry_price=100.0,
        entry_delta=0.55,
        current_price=105.0,
        quantity=75,
        entry_time=datetime.now()
    )


@pytest.fixture
def tick_data_sequence():
    """Provide sequence of ticks for strategy testing"""
    return [
        MockTick.sample(ltp=100.0, volume=1000, oi=500000),
        MockTick.sample(ltp=101.0, volume=1100, oi=510000),
        MockTick.sample(ltp=102.0, volume=1200, oi=520000),
        MockTick.sample(ltp=101.5, volume=1150, oi=515000),
        MockTick.sample(ltp=103.0, volume=1300, oi=530000),
    ]
