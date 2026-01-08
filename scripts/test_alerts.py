#!/usr/bin/env python3
"""
Test Alert System
Demonstrates Telegram and console notifications

Setup:
1. Create a Telegram bot via @BotFather
2. Get bot token
3. Get your chat ID (send message to @userinfobot)
4. Add to .env:
   TELEGRAM_BOT_TOKEN=your_bot_token
   TELEGRAM_CHAT_ID=your_chat_id
   TELEGRAM_ALERTS_ENABLED=true

Run: PYTHONPATH=. .venv/bin/python scripts/test_alerts.py
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.alert_system import get_alert_system, AlertLevel


def test_alerts():
    """Test all alert types"""
    print("=" * 80)
    print("  ALERT SYSTEM TEST")
    print("=" * 80)
    
    # Get alert system
    alert = get_alert_system()
    
    print(f"\nTelegram Enabled: {alert.telegram_enabled}")
    if alert.telegram_enabled:
        print(f"Bot Token: {alert.telegram_bot_token[:20]}...")
        print(f"Chat ID: {alert.telegram_chat_id}")
    else:
        print("⚠️  Telegram disabled (check .env for credentials)")
    
    print("\n" + "-" * 80)
    print("Testing alerts...")
    print("-" * 80)
    
    # Test 1: Basic info alert
    print("\n1. Info Alert")
    alert.send_alert("Angel-X Strategy Started", AlertLevel.INFO)
    time.sleep(1)
    
    # Test 2: Entry signal
    print("\n2. Entry Signal Alert")
    alert.entry_signal(
        strike="26200",
        option_type="CE",
        bias="BULLISH",
        price=125.50,
        greeks={
            "delta": 0.472,
            "gamma": 0.00181,
            "theta": -45.92,
            "vega": 5.45,
            "iv": 0.16
        }
    )
    time.sleep(1)
    
    # Test 3: Trade executed
    print("\n3. Trade Executed Alert")
    alert.trade_executed(
        strike="26200 CE",
        option_type="CALL",
        action="BUY",
        quantity=75,
        price=125.50
    )
    time.sleep(1)
    
    # Test 4: Target achieved
    print("\n4. Target Achieved Alert")
    alert.target_achieved(
        strike="26200",
        option_type="CE",
        entry_price=125.50,
        exit_price=150.00,
        pnl=1837.50
    )
    time.sleep(1)
    
    # Test 5: Stop loss hit
    print("\n5. Stop Loss Alert")
    alert.stop_loss_hit(
        strike="26250",
        option_type="CE",
        entry_price=100.00,
        exit_price=85.00,
        pnl=-1125.00
    )
    time.sleep(1)
    
    # Test 6: Position update
    print("\n6. Position Update Alert")
    alert.position_update(
        positions=2,
        total_pnl=712.50,
        realized_pnl=1837.50,
        unrealized_pnl=-1125.00
    )
    time.sleep(1)
    
    # Test 7: Risk alert
    print("\n7. Risk Alert")
    alert.risk_alert(
        alert_type="Daily Loss Limit",
        current_value=450.00,
        threshold=500.00,
        action="Trading paused"
    )
    time.sleep(1)
    
    # Test 8: Greeks threshold breach
    print("\n8. Greeks Alert")
    alert.greeks_threshold_breach(
        greek_type="Portfolio Delta",
        current=520.0,
        threshold=500.0,
        position="26200 CE + 26250 CE"
    )
    time.sleep(1)
    
    # Test 9: Daily summary
    print("\n9. Daily Summary Alert")
    alert.daily_summary(
        trades=8,
        wins=5,
        losses=3,
        pnl=2450.00,
        win_rate=62.5
    )
    time.sleep(1)
    
    # Test 10: System event
    print("\n10. System Event Alert")
    alert.system_event(
        event="Data Feed Connection",
        status="OK",
        details="Connected to AngelOne WebSocket"
    )
    time.sleep(1)
    
    # Summary
    print("\n" + "=" * 80)
    print("  TEST SUMMARY")
    print("=" * 80)
    print(f"\nTotal Alerts Sent: {alert.alert_count}")
    print(f"Last Alert Time: {alert.last_alert_time}")
    print("\n✅ Alert system test complete!")
    
    if alert.telegram_enabled:
        print("\n📱 Check your Telegram for notifications")
    else:
        print("\n💡 To enable Telegram:")
        print("   1. Create bot via @BotFather")
        print("   2. Get chat ID from @userinfobot")
        print("   3. Add to .env:")
        print("      TELEGRAM_BOT_TOKEN=your_token")
        print("      TELEGRAM_CHAT_ID=your_chat_id")
        print("      TELEGRAM_ALERTS_ENABLED=true")


if __name__ == "__main__":
    test_alerts()
