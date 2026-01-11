"""
Mock objects for testing
"""

from unittest.mock import Mock, MagicMock
from datetime import datetime


class MockDataFeed:
    """Mock WebSocket data feed"""
    def __init__(self):
        self.connected = True
        self.data_buffer = []
        
    def connect(self):
        return True
    
    def subscribe(self, symbol):
        return True
    
    def get_latest(self, symbol):
        return {'ltp': 100.0, 'bid': 99.5, 'ask': 100.5}
    
    def disconnect(self):
        self.connected = False


class MockOrderManager:
    """Mock order execution"""
    def __init__(self):
        self.orders = []
        self.order_id = 1000
        
    def place_order(self, symbol, order_type, quantity, price=None):
        order = {
            'order_id': self.order_id,
            'symbol': symbol,
            'type': order_type,
            'quantity': quantity,
            'price': price,
            'status': 'FILLED',
            'timestamp': datetime.now()
        }
        self.orders.append(order)
        self.order_id += 1
        return order
    
    def cancel_order(self, order_id):
        for order in self.orders:
            if order['order_id'] == order_id:
                order['status'] = 'CANCELLED'
                return True
        return False
    
    def get_order_status(self, order_id):
        for order in self.orders:
            if order['order_id'] == order_id:
                return order['status']
        return None


class MockTradeManager:
    """Mock trade management"""
    def __init__(self):
        self.positions = {}
        
    def open_position(self, symbol, order_result):
        self.positions[symbol] = {
            'symbol': symbol,
            'entry_price': order_result.get('price', 100.0),
            'quantity': order_result.get('quantity', 75),
            'entry_time': datetime.now(),
            'status': 'OPEN'
        }
        return self.positions[symbol]
    
    def close_position(self, symbol, exit_price):
        if symbol in self.positions:
            pos = self.positions[symbol]
            pnl = (exit_price - pos['entry_price']) * pos['quantity']
            pos['exit_price'] = exit_price
            pos['exit_time'] = datetime.now()
            pos['pnl'] = pnl
            pos['status'] = 'CLOSED'
            return pos
        return None
    
    def get_position(self, symbol):
        return self.positions.get(symbol)


class MockGreeksManager:
    """Mock Greeks calculation"""
    def __init__(self):
        self.greeks = {}
    
    def calculate_greeks(self, option_symbol, spot, iv):
        return {
            'delta': 0.55,
            'gamma': 0.003,
            'theta': -0.02,
            'vega': 0.05,
            'iv': iv
        }
    
    def update_greeks(self, ticks):
        return True


class MockBiasEngine:
    """Mock market bias detection"""
    def __init__(self):
        self.bias = None
    
    def analyze(self, tick_data, greeks):
        # Simple mock logic
        if tick_data['ltp'] > 100:
            self.bias = 'BULLISH'
        elif tick_data['ltp'] < 100:
            self.bias = 'BEARISH'
        else:
            self.bias = 'NEUTRAL'
        return self.bias


class MockEntryEngine:
    """Mock entry signal generation"""
    def __init__(self):
        self.last_signal = None
    
    def should_enter(self, bias, greeks, tick):
        if bias == 'BULLISH' and greeks['delta'] > 0.45:
            self.last_signal = {'action': 'BUY', 'confidence': 0.8}
            return True
        return False


# Helper to create mock brokers
def create_mock_broker():
    """Create a complete mock broker setup"""
    broker = MagicMock()
    broker.place_order.return_value = {'status': 'success', 'order_id': 1001}
    broker.cancel_order.return_value = {'status': 'success'}
    broker.get_position.return_value = {'symbol': 'TEST', 'qty': 100, 'price': 100}
    broker.get_margin.return_value = {'available': 50000, 'used': 50000}
    return broker
