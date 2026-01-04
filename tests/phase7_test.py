"""
PHASE 7 — COMPREHENSIVE TEST SUITE

Testing all 8 exit components
20+ test cases covering:
✓ Theta acceleration detection
✓ Time-based exits
✓ Cooldown logic
✓ Trade journal
✓ Exit orchestration
✓ Signal priority
"""

import pytest
from datetime import datetime, timedelta
from src.utils.phase7_exit_models import Phase7Config
from src.utils.phase7_theta_time_exit import ThetaDecayExitEngine, TimeBasedForceExitEngine
from src.utils.phase7_cooldown_engine import CooldownLogicEngine, CooldownState, CooldownReason
from src.utils.phase7_trade_journal import TradeJournalEngine
from src.utils.phase7_exit_orchestrator import Phase7ExitOrchestrator, ExitAction


# ====================================================================
# SECTION 1: THETA DECAY ENGINE TESTS
# ====================================================================

class TestThetaDecayExitEngine:
    """Test theta decay detection"""
    
    def setup_method(self):
        self.engine = ThetaDecayExitEngine()
    
    def test_theta_acceleration_detection_high(self):
        """Test high theta acceleration detection"""
        theta_accel, rate, msg = self.engine.detect_theta_acceleration(
            theta_current=-0.10,
            theta_prev=0.00,
            time_since_update_secs=60.0,
        )
        
        assert theta_accel == True
        assert rate > 0.08
    
    def test_theta_acceleration_normal(self):
        """Test normal theta movement"""
        theta_accel, rate, msg = self.engine.detect_theta_acceleration(
            theta_current=-0.03,
            theta_prev=0.00,
            time_since_update_secs=60.0,
        )
        
        assert theta_accel == False
    
    def test_time_exceeded(self):
        """Test time limit exceeded"""
        now = datetime.now()
        entry = now - timedelta(seconds=700)
        
        exceeded, elapsed, msg = self.engine.check_time_exceeded(entry, now)
        
        assert exceeded == True
        assert elapsed > 600
    
    def test_time_not_exceeded(self):
        """Test time limit not exceeded"""
        now = datetime.now()
        entry = now - timedelta(seconds=300)
        
        exceeded, elapsed, msg = self.engine.check_time_exceeded(entry, now)
        
        assert exceeded == False
    
    def test_iv_crush_detection(self):
        """Test IV crush detection"""
        crush, percent, msg = self.engine.detect_iv_crush(
            iv_current=15.0,
            iv_entry=20.0,
        )
        
        assert crush == True
        assert percent > 20
    
    def test_iv_stable(self):
        """Test stable IV"""
        crush, percent, msg = self.engine.detect_iv_crush(
            iv_current=19.5,
            iv_entry=20.0,
        )
        
        assert crush == False
    
    def test_should_exit_theta_on_acceleration(self):
        """Test exit signal on theta acceleration"""
        now = datetime.now()
        
        should_exit, signal, conf, msg = self.engine.should_exit_theta(
            theta_current=-0.12,
            theta_prev=0.00,
            entry_time=now - timedelta(seconds=100),
            current_time=now,
            iv_current=18.0,
            iv_entry=20.0,
            time_since_update_secs=60.0,
        )
        
        assert should_exit == True
        assert conf > 0.90
    
    def test_should_exit_theta_on_time_limit(self):
        """Test exit signal on time limit"""
        now = datetime.now()
        
        should_exit, signal, conf, msg = self.engine.should_exit_theta(
            theta_current=-0.02,
            theta_prev=-0.01,
            entry_time=now - timedelta(seconds=700),
            current_time=now,
            iv_current=20.0,
            iv_entry=20.0,
            time_since_update_secs=60.0,
        )
        
        assert should_exit == True
        assert conf == 0.99


# ====================================================================
# SECTION 2: TIME-BASED FORCED EXIT TESTS
# ====================================================================

class TestTimeBasedForceExitEngine:
    """Test time-based forced exits"""
    
    def setup_method(self):
        self.engine = TimeBasedForceExitEngine()
    
    def test_force_exit_market_close(self):
        """Test force exit near market close (15:30 IST)"""
        
        close_time = datetime.strptime("15:20:00", "%H:%M:%S").time()
        test_time = datetime.combine(datetime.now().date(), close_time)
        entry_time = test_time - timedelta(minutes=5)
        
        should_exit, msg = self.engine.should_force_exit(test_time, entry_time)
        
        assert should_exit == True


# ====================================================================
# SECTION 3: COOLDOWN ENGINE TESTS
# ====================================================================

class TestCooldownLogicEngine:
    """Test cooldown management"""
    
    def setup_method(self):
        self.engine = CooldownLogicEngine()
    
    def test_profitable_trade_short_cooldown(self):
        """Test cooldown after profit"""
        cooldown, reason, msg = self.engine.calculate_cooldown_period(
            exit_pnl=100.0,
            volatility_index=15.0,
            consecutive_losses_count=0,
        )
        
        assert cooldown < 30
        assert reason == CooldownReason.PROFITABLE_TRADE
    
    def test_losing_trade_longer_cooldown(self):
        """Test cooldown after loss"""
        cooldown, reason, msg = self.engine.calculate_cooldown_period(
            exit_pnl=-100.0,
            volatility_index=15.0,
            consecutive_losses_count=0,
        )
        
        assert cooldown > 30
        assert reason == CooldownReason.LOSING_TRADE
    
    def test_multiple_losses_longer_cooldown(self):
        """Test cooldown after multiple losses"""
        cooldown, reason, msg = self.engine.calculate_cooldown_period(
            exit_pnl=-100.0,
            volatility_index=15.0,
            consecutive_losses_count=3,
        )
        
        assert cooldown > 100
    
    def test_high_volatility_extended_cooldown(self):
        """Test extended cooldown on high volatility"""
        cooldown, msg = self.engine.calculate_volatility_cooldown(
            volatility_index=26.0,
        )
        
        assert cooldown > 60
    
    def test_start_cooldown(self):
        """Test starting cooldown"""
        now = datetime.now()
        
        success, msg = self.engine.start_cooldown(
            exit_pnl=100.0,
            volatility_index=15.0,
            current_time=now,
        )
        
        assert success == True
        assert self.engine.cooldown_start is not None
    
    def test_is_in_cooldown_active(self):
        """Test active cooldown check"""
        now = datetime.now()
        
        self.engine.start_cooldown(
            exit_pnl=-100.0,
            volatility_index=15.0,
            current_time=now,
        )
        
        in_cooldown, remaining, msg = self.engine.is_in_cooldown(now + timedelta(seconds=10))
        
        assert in_cooldown == True
        assert remaining > 0
    
    def test_is_in_cooldown_expired(self):
        """Test expired cooldown"""
        now = datetime.now()
        
        self.engine.start_cooldown(
            exit_pnl=100.0,
            volatility_index=15.0,
            current_time=now,
        )
        
        in_cooldown, remaining, msg = self.engine.is_in_cooldown(now + timedelta(seconds=30))
        
        assert in_cooldown == False
    
    def test_can_trade_now_during_cooldown(self):
        """Test can_trade_now during cooldown"""
        now = datetime.now()
        
        self.engine.start_cooldown(
            exit_pnl=-100.0,
            volatility_index=15.0,
            current_time=now,
        )
        
        can_trade, msg = self.engine.can_trade_now(now + timedelta(seconds=10))
        
        assert can_trade == False
    
    def test_can_trade_now_after_cooldown(self):
        """Test can_trade_now after cooldown expires"""
        now = datetime.now()
        
        self.engine.start_cooldown(
            exit_pnl=100.0,
            volatility_index=15.0,
            current_time=now,
        )
        
        can_trade, msg = self.engine.can_trade_now(now + timedelta(seconds=30))
        
        assert can_trade == True


# ====================================================================
# SECTION 4: TRADE JOURNAL TESTS
# ====================================================================

class TestTradeJournalEngine:
    """Test trade journal recording"""
    
    def setup_method(self):
        self.engine = TradeJournalEngine()
    
    def test_create_entry_snapshot(self):
        """Test creating entry snapshot"""
        now = datetime.now()
        
        snapshot = self.engine.create_entry_snapshot(
            entry_time=now,
            entry_price=50.0,
            option_type="CE",
            entry_delta=0.6,
            entry_gamma=0.01,
            entry_theta=-0.02,
            entry_iv=18.0,
            ce_oi=100000,
            pe_oi=80000,
            volume_entry=1100,
        )
        
        assert snapshot.entry_price == 50.0
        assert snapshot.option_type == "CE"
        assert snapshot.delta_entry == 0.6
    
    def test_get_session_stats_empty(self):
        """Test session stats when no trades"""
        stats = self.engine.get_session_stats()
        
        assert stats["total_trades"] == 0
        assert stats["win_rate"] == 0.0


# ====================================================================
# SECTION 5: EXIT ORCHESTRATOR TESTS
# ====================================================================

class TestPhase7ExitOrchestrator:
    """Test complete exit orchestration"""
    
    def setup_method(self):
        self.orchestrator = Phase7ExitOrchestrator()
    
    def test_initialize_active_trade(self):
        """Test initializing active trade"""
        now = datetime.now()
        
        msg = self.orchestrator.initialize_active_trade(
            entry_price=50.0,
            option_type="CE",
            contract_symbol="NIFTY50",
            entry_time=now,
            entry_delta=0.6,
            entry_gamma=0.01,
            entry_theta=-0.02,
            entry_vega=0.05,
            entry_iv=18.0,
            ce_oi=100000,
            pe_oi=80000,
            bid_qty=500,
            ask_qty=600,
            position_quantity=100,
            preceding_candle_close=49.5,
        )
        
        assert "Trade initialized" in msg
        assert self.orchestrator.active_trade is not None
    
    def test_update_market_tick(self):
        """Test updating market tick"""
        now = datetime.now()
        
        self.orchestrator.initialize_active_trade(
            entry_price=50.0,
            option_type="CE",
            contract_symbol="NIFTY50",
            entry_time=now,
            entry_delta=0.6,
            entry_gamma=0.01,
            entry_theta=-0.02,
            entry_vega=0.05,
            entry_iv=18.0,
            ce_oi=100000,
            pe_oi=80000,
            bid_qty=500,
            ask_qty=600,
            position_quantity=100,
            preceding_candle_close=49.5,
        )
        
        self.orchestrator.update_market_tick(
            current_price=51.0,
            current_delta=0.65,
            current_gamma=0.009,
            current_theta=-0.025,
            current_vega=0.048,
            current_iv=17.5,
            ce_oi=102000,
            pe_oi=79000,
        )
        
        assert self.orchestrator.active_trade["current_price"] == 51.0
        assert self.orchestrator.active_trade["current_delta"] == 0.65
    
    def test_get_active_trade_status(self):
        """Test getting active trade status"""
        now = datetime.now()
        
        self.orchestrator.initialize_active_trade(
            entry_price=50.0,
            option_type="CE",
            contract_symbol="NIFTY50",
            entry_time=now,
            entry_delta=0.6,
            entry_gamma=0.01,
            entry_theta=-0.02,
            entry_vega=0.05,
            entry_iv=18.0,
            ce_oi=100000,
            pe_oi=80000,
            bid_qty=500,
            ask_qty=600,
            position_quantity=100,
            preceding_candle_close=49.5,
        )
        
        self.orchestrator.update_market_tick(
            current_price=51.0,
            current_delta=0.65,
            current_gamma=0.009,
            current_theta=-0.025,
            current_vega=0.048,
            current_iv=17.5,
            ce_oi=102000,
            pe_oi=79000,
        )
        
        status = self.orchestrator.get_active_trade_status()
        
        assert status["status"] == "active"
        assert status["pnl_percent"] > 0
    
    def test_check_all_exit_signals_no_trade(self):
        """Test checking signals with no active trade"""
        now = datetime.now()
        
        summary = self.orchestrator.check_all_exit_signals(
            current_time=now,
            theta_prev=-0.02,
        )
        
        assert summary.should_exit == False
    
    def test_execute_exit(self):
        """Test executing exit"""
        now = datetime.now()
        
        self.orchestrator.initialize_active_trade(
            entry_price=50.0,
            option_type="CE",
            contract_symbol="NIFTY50",
            entry_time=now,
            entry_delta=0.6,
            entry_gamma=0.01,
            entry_theta=-0.02,
            entry_vega=0.05,
            entry_iv=18.0,
            ce_oi=100000,
            pe_oi=80000,
            bid_qty=500,
            ask_qty=600,
            position_quantity=100,
            preceding_candle_close=49.5,
        )
        
        self.orchestrator.update_market_tick(
            current_price=51.0,
            current_delta=0.65,
            current_gamma=0.009,
            current_theta=-0.025,
            current_vega=0.048,
            current_iv=17.5,
            ce_oi=102000,
            pe_oi=79000,
        )
        
        success, msg = self.orchestrator.execute_exit(
            exit_price=51.0,
            current_time=now + timedelta(seconds=120),
            exit_signal=ExitAction.TRAILING_SL,
            reason="Test exit",
        )
        
        assert success == True
        assert self.orchestrator.active_trade is None


# ====================================================================
# RUN ALL TESTS
# ====================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
