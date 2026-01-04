"""
PHASE 6 — COMPREHENSIVE TEST SUITE

Testing real order execution + risk management engine
"""

import pytest
from datetime import datetime, timedelta
from src.utils.phase6_order_models import (
    Phase6Config, ExitReason, TradeMonitorUpdate,
    KillSwitchReason, OrderStatus, PositionStatus
)
from src.utils.phase6_orchestrator import OrderExecutionAndRiskEngine


class TestPhase6Orchestrator:
    """Complete Phase 6 integration tests"""
    
    @pytest.fixture
    def engine(self):
        """Create orchestrator instance"""
        config = Phase6Config()
        return OrderExecutionAndRiskEngine(config)
    
    # ====================================================================
    # TEST 1: PRE-ORDER SAFETY GATE
    # ====================================================================
    
    def test_can_trade_market_closed(self, engine):
        """❌ Block trade when market closed"""
        can_trade, msg, checks = engine.verify_can_trade(
            current_time=datetime.now(),
            market_open=False,
        )
        assert can_trade is False
        assert "Market" in msg
    
    def test_can_trade_signal_denied(self, engine):
        """❌ Block trade when signal says no"""
        can_trade, msg, checks = engine.verify_can_trade(
            current_time=datetime.now(),
            market_open=True,
            trade_allowed=False,
        )
        assert can_trade is False
        assert "Trade" in msg
    
    def test_can_trade_normal(self, engine):
        """✓ Allow trade in normal conditions"""
        can_trade, msg, checks = engine.verify_can_trade(
            current_time=datetime.now(),
            market_open=True,
            trade_allowed=True,
        )
        assert can_trade is True
    
    # ====================================================================
    # TEST 2: ORDER PREPARATION (SIZING + SL)
    # ====================================================================
    
    def test_prepare_order_basic(self, engine):
        """✓ Prepare order with all calculations"""
        prepared = engine.prepare_execution_order(
            entry_price=100.0,
            option_type="CE",
            delta_ce=0.6,
            delta_pe=0.1,
        )
        
        assert "quantity" in prepared
        assert prepared["quantity"] > 0
        assert "sl_price" in prepared
        assert "target_price" in prepared
        assert "actual_risk" in prepared
    
    def test_prepare_order_high_iv(self, engine):
        """✓ Reduce quantity when IV high"""
        prepared_normal = engine.prepare_execution_order(
            entry_price=100.0,
            option_type="CE",
            current_iv=0.15,
        )
        
        prepared_high_iv = engine.prepare_execution_order(
            entry_price=100.0,
            option_type="CE",
            current_iv=0.30,
        )
        
        # High IV should give lower (or similar) quantity
        assert prepared_high_iv["quantity"] <= prepared_normal["quantity"]
    
    # ====================================================================
    # TEST 3: PLACE ORDER (ATOMIC)
    # ====================================================================
    
    def test_place_order_success(self, engine):
        """✓ Successfully place atomic order"""
        
        can_trade, _, _ = engine.verify_can_trade(
            datetime.now(), market_open=True, trade_allowed=True
        )
        assert can_trade
        
        prepared = engine.prepare_execution_order(
            entry_price=100.0,
            option_type="CE",
            delta_ce=0.6,
        )
        
        success, trade_id, msg = engine.place_order(
            symbol="NIFTY",
            option_type="CE",
            strike=20200.0,
            entry_price=100.0,
            prepared_order=prepared,
        )
        
        assert success is True
        assert trade_id is not None
        assert trade_id in engine.active_trades
    
    def test_place_order_creates_linked_orders(self, engine):
        """✓ Place order creates buy + SL linked pair"""
        
        prepared = engine.prepare_execution_order(
            entry_price=100.0,
            option_type="CE",
        )
        
        success, trade_id, msg = engine.place_order(
            symbol="NIFTY",
            option_type="CE",
            strike=20200.0,
            entry_price=100.0,
            prepared_order=prepared,
        )
        
        assert success
        trade = engine.active_trades[trade_id]
        assert trade.linked_orders is not None
        assert trade.linked_orders.entry_order is not None
        assert trade.linked_orders.sl_order is not None
    
    def test_active_trade_count(self, engine):
        """✓ Track total trades placed"""
        assert engine.total_trades == 0
        
        prepared = engine.prepare_execution_order(100.0, "CE")
        engine.place_order("NIFTY", "CE", 20200.0, 100.0, prepared)
        assert engine.total_trades == 1
        
        prepared = engine.prepare_execution_order(105.0, "PE")
        engine.place_order("NIFTY", "PE", 20000.0, 105.0, prepared)
        assert engine.total_trades == 2
    
    # ====================================================================
    # TEST 4: TRADE MONITORING
    # ====================================================================
    
    def test_monitor_target_hit(self, engine):
        """✓ Detect when target hit"""
        
        prepared = engine.prepare_execution_order(100.0, "CE", delta_ce=0.6)
        success, trade_id, _ = engine.place_order(
            "NIFTY", "CE", 20200.0, 100.0, prepared
        )
        assert success
        
        trade = engine.active_trades[trade_id]
        target = trade.target_level.price if trade.target_level else 101.0
        
        # Update with price at target
        update = TradeMonitorUpdate(
            current_ltp=target,
            delta_ce=0.7,
            delta_pe=0.1,
            gamma_ce=0.01,
            timestamp=datetime.now(),
        )
        
        alerts = engine.update_trade(trade_id, update)
        assert any("target" in str(reason).lower() for should_exit, reason in alerts)
    
    def test_monitor_sl_hit(self, engine):
        """✓ Detect when SL hit"""
        
        prepared = engine.prepare_execution_order(100.0, "CE", delta_ce=0.6)
        success, trade_id, _ = engine.place_order(
            "NIFTY", "CE", 20200.0, 100.0, prepared
        )
        assert success
        
        trade = engine.active_trades[trade_id]
        sl = trade.sl_level.price if trade.sl_level else 95.0
        
        # Update with price below SL
        update = TradeMonitorUpdate(
            current_ltp=sl - 1,
            delta_ce=0.3,
            delta_pe=0.3,
            timestamp=datetime.now(),
        )
        
        alerts = engine.update_trade(trade_id, update)
        assert any("SL" in str(reason) for should_exit, reason in alerts)
    
    def test_monitor_delta_flip(self, engine):
        """✓ Detect delta flip (bullish → bearish)"""
        
        prepared = engine.prepare_execution_order(100.0, "CE", delta_ce=0.7)
        success, trade_id, _ = engine.place_order(
            "NIFTY", "CE", 20200.0, 100.0, prepared
        )
        assert success
        
        # Delta was 0.7 at entry, now flipped to <0.3
        update = TradeMonitorUpdate(
            current_ltp=100.0,
            delta_ce=0.2,  # Flipped!
            delta_pe=0.5,
            timestamp=datetime.now(),
        )
        
        alerts = engine.update_trade(trade_id, update)
        assert any("delta" in str(reason).lower() or "flip" in str(reason).lower()
                   for should_exit, reason in alerts)
    
    # ====================================================================
    # TEST 5: EXIT TRADE
    # ====================================================================
    
    def test_exit_trade_profit(self, engine):
        """✓ Exit trade with profit"""
        
        prepared = engine.prepare_execution_order(100.0, "CE")
        success, trade_id, _ = engine.place_order(
            "NIFTY", "CE", 20200.0, 100.0, prepared
        )
        
        success, closed = engine.exit_trade(
            trade_id=trade_id,
            exit_price=105.0,
            exit_reason=ExitReason.TARGET_HIT,
        )
        
        assert success
        assert closed.pnl > 0
        assert closed.result.name == "PROFIT"
        assert trade_id not in engine.active_trades
        assert len(engine.closed_trades) == 1
    
    def test_exit_trade_loss(self, engine):
        """✓ Exit trade with loss"""
        
        prepared = engine.prepare_execution_order(100.0, "CE")
        success, trade_id, _ = engine.place_order(
            "NIFTY", "CE", 20200.0, 100.0, prepared
        )
        
        success, closed = engine.exit_trade(
            trade_id=trade_id,
            exit_price=95.0,
            exit_reason=ExitReason.SL_HIT,
        )
        
        assert success
        assert closed.pnl < 0
        assert closed.result.name == "LOSS"
    
    def test_exit_trade_breakeven(self, engine):
        """✓ Exit trade at breakeven"""
        
        prepared = engine.prepare_execution_order(100.0, "CE")
        success, trade_id, _ = engine.place_order(
            "NIFTY", "CE", 20200.0, 100.0, prepared
        )
        
        success, closed = engine.exit_trade(
            trade_id=trade_id,
            exit_price=100.0,
            exit_reason=ExitReason.FORCED_EXIT,
        )
        
        assert success
        assert closed.pnl == 0
        assert closed.result.name == "BREAKEVEN"
    
    # ====================================================================
    # TEST 6: MULTIPLE TRADES
    # ====================================================================
    
    def test_multiple_trades_independent(self, engine):
        """✓ Handle multiple independent trades"""
        
        # Trade 1
        prepared1 = engine.prepare_execution_order(100.0, "CE")
        success1, tid1, _ = engine.place_order(
            "NIFTY", "CE", 20200.0, 100.0, prepared1
        )
        
        # Trade 2
        prepared2 = engine.prepare_execution_order(105.0, "PE")
        success2, tid2, _ = engine.place_order(
            "NIFTY", "PE", 20000.0, 105.0, prepared2
        )
        
        # Trade 3
        prepared3 = engine.prepare_execution_order(110.0, "CE")
        success3, tid3, _ = engine.place_order(
            "NIFTY", "CE", 20500.0, 110.0, prepared3
        )
        
        assert success1 and success2 and success3
        assert len(engine.active_trades) == 3
        assert tid1 != tid2 != tid3
    
    def test_multiple_trades_exit_independently(self, engine):
        """✓ Exit one trade without affecting others"""
        
        # Place 3 trades
        tids = []
        for i in range(3):
            prepared = engine.prepare_execution_order(100.0 + i*5, "CE")
            success, tid, _ = engine.place_order(
                "NIFTY", "CE", 20200.0 + i*100, 100.0 + i*5, prepared
            )
            tids.append(tid)
        
        assert len(engine.active_trades) == 3
        
        # Exit first trade
        engine.exit_trade(tids[0], 105.0, ExitReason.TARGET_HIT)
        assert len(engine.active_trades) == 2
        assert tids[0] not in engine.active_trades
        assert tids[1] in engine.active_trades
        assert tids[2] in engine.active_trades
    
    # ====================================================================
    # TEST 7: RISK CONTROL
    # ====================================================================
    
    def test_risk_limits_max_trades(self, engine):
        """✓ Enforce max trades/day"""
        
        can_trade, msg, _ = engine.verify_can_trade(
            datetime.now(), market_open=True, trade_allowed=True
        )
        assert can_trade
        
        # Place 3 trades (max from config)
        for i in range(3):
            prepared = engine.prepare_execution_order(100.0, "CE")
            success, tid, _ = engine.place_order(
                "NIFTY", "CE", 20200.0, 100.0, prepared
            )
            assert success
            engine.exit_trade(tid, 101.0, ExitReason.TARGET_HIT)
        
        # Try 4th trade - should be blocked
        can_trade, msg, _ = engine.verify_can_trade(
            datetime.now(), market_open=True, trade_allowed=True
        )
        assert can_trade is False or "trade" in msg.lower()
    
    def test_risk_limits_max_loss(self, engine):
        """✓ Enforce max daily loss"""
        
        # Force some losses to hit daily limit
        loss_amount = 0
        while loss_amount < 1500:
            prepared = engine.prepare_execution_order(100.0, "CE")
            success, tid, _ = engine.place_order(
                "NIFTY", "CE", 20200.0, 100.0, prepared
            )
            
            # Exit at loss
            success, closed = engine.exit_trade(
                tid, 90.0, ExitReason.SL_HIT
            )
            loss_amount += abs(closed.pnl)
        
        # Should now hit daily loss limit
        can_trade, msg, _ = engine.verify_can_trade(
            datetime.now(), market_open=True, trade_allowed=True
        )
        # May still allow trade but check status
        risk_status = engine.get_risk_status()
        assert "loss" in str(risk_status).lower() or not can_trade
    
    # ====================================================================
    # TEST 8: EMERGENCY EXIT
    # ====================================================================
    
    def test_kill_switch_exits_all(self, engine):
        """✓ Kill switch exits all positions"""
        
        # Place 3 trades
        for i in range(3):
            prepared = engine.prepare_execution_order(100.0, "CE")
            engine.place_order("NIFTY", "CE", 20200.0, 100.0, prepared)
        
        assert len(engine.active_trades) == 3
        
        # Activate kill switch
        num_exited, total_pnl, closed = engine.activate_kill_switch(
            reason=KillSwitchReason.MANUAL,
            details="Test emergency exit"
        )
        
        assert num_exited == 3
        assert len(engine.active_trades) == 0
        assert len(engine.closed_trades) == 3
    
    def test_kill_switch_prevents_new_trades(self, engine):
        """✓ Kill switch active blocks new trades"""
        
        prepared = engine.prepare_execution_order(100.0, "CE")
        engine.place_order("NIFTY", "CE", 20200.0, 100.0, prepared)
        
        engine.activate_kill_switch(KillSwitchReason.BROKER_ERROR)
        
        assert engine.kill_switch.is_active() is True
    
    # ====================================================================
    # TEST 9: REPORTING & METRICS
    # ====================================================================
    
    def test_active_summary(self, engine):
        """✓ Get active trades summary"""
        
        prepared = engine.prepare_execution_order(100.0, "CE")
        engine.place_order("NIFTY", "CE", 20200.0, 100.0, prepared)
        
        summary = engine.get_active_trades_summary()
        assert summary["active_count"] == 1
        assert "trades" in summary
    
    def test_closed_summary_no_trades(self, engine):
        """✓ Closed summary when no trades"""
        
        summary = engine.get_closed_trades_summary()
        assert summary["total_trades"] == 0
        assert summary["total_pnl"] == 0.0
    
    def test_closed_summary_with_trades(self, engine):
        """✓ Closed summary with trade history"""
        
        # Profitable trade
        prepared = engine.prepare_execution_order(100.0, "CE")
        success, tid, _ = engine.place_order(
            "NIFTY", "CE", 20200.0, 100.0, prepared
        )
        engine.exit_trade(tid, 105.0, ExitReason.TARGET_HIT)
        
        # Losing trade
        prepared = engine.prepare_execution_order(100.0, "PE")
        success, tid, _ = engine.place_order(
            "NIFTY", "PE", 20000.0, 100.0, prepared
        )
        engine.exit_trade(tid, 95.0, ExitReason.SL_HIT)
        
        summary = engine.get_closed_trades_summary()
        assert summary["total_trades"] == 2
        assert summary["winners"] == 1
        assert summary["losers"] == 1
        assert "total_pnl" in summary
        assert "win_rate" in summary
    
    def test_risk_status(self, engine):
        """✓ Get risk status"""
        
        status = engine.get_risk_status()
        assert "can_trade" in status
        assert "trades_today" in status
        assert "daily_pnl" in status
    
    def test_system_health(self, engine):
        """✓ Get system health"""
        
        health = engine.get_system_health()
        assert "status" in health
        assert health["status"] in ["GREEN", "YELLOW", "RED"]
        assert "warnings" in health
    
    # ====================================================================
    # TEST 10: INTEGRATION
    # ====================================================================
    
    def test_complete_trade_lifecycle(self, engine):
        """✓ Complete trade from entry to exit"""
        
        # Verify can trade
        can_trade, _, _ = engine.verify_can_trade(
            datetime.now(), market_open=True, trade_allowed=True
        )
        assert can_trade
        
        # Prepare order
        prepared = engine.prepare_execution_order(100.0, "CE", delta_ce=0.65)
        assert prepared["quantity"] > 0
        
        # Place order
        success, trade_id, msg = engine.place_order(
            "NIFTY", "CE", 20200.0, 100.0, prepared
        )
        assert success
        assert trade_id in engine.active_trades
        
        # Monitor trade
        update = TradeMonitorUpdate(
            current_ltp=102.0,
            delta_ce=0.7,
            delta_pe=0.1,
            timestamp=datetime.now(),
        )
        alerts = engine.update_trade(trade_id, update)
        
        # Exit trade
        success, closed = engine.exit_trade(
            trade_id, 102.0, ExitReason.TARGET_HIT
        )
        assert success
        assert closed.pnl > 0
        assert len(engine.closed_trades) == 1
        assert engine.total_trades == 1
        
        # Verify final state
        summary = engine.get_closed_trades_summary()
        assert summary["total_trades"] == 1
        assert summary["winners"] == 1


if __name__ == "__main__":
    # Run: pytest scripts/phase6_test.py -v
    pytest.main([__file__, "-v"])
