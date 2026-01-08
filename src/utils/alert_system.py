"""
Alert System for Angel-X Strategy
Supports Telegram and console notifications for trade events
"""

import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
import requests

from src.utils.logger import StrategyLogger

logger = StrategyLogger.get_logger(__name__)


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "ℹ️"
    SUCCESS = "✅"
    WARNING = "⚠️"
    ERROR = "❌"
    TRADE = "📈"
    PROFIT = "💰"
    LOSS = "📉"


class AlertSystem:
    """
    Multi-channel alert system for strategy events
    
    Supports:
    - Telegram notifications
    - Console logging
    - Future: WhatsApp, Email, SMS
    """
    
    def __init__(self, telegram_enabled: bool = True):
        """
        Initialize alert system
        
        Args:
            telegram_enabled: Enable Telegram notifications
        """
        self.telegram_enabled = telegram_enabled
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        # Validate Telegram config
        if self.telegram_enabled:
            if not self.telegram_bot_token or not self.telegram_chat_id:
                logger.warning("Telegram enabled but credentials missing. Disabling Telegram alerts.")
                self.telegram_enabled = False
            else:
                logger.info("Telegram alerts enabled")
        
        # Alert history
        self.alert_count = 0
        self.last_alert_time = None
    
    def send_alert(
        self,
        message: str,
        level: AlertLevel = AlertLevel.INFO,
        data: Optional[Dict[str, Any]] = None,
        silent: bool = False
    ) -> bool:
        """
        Send alert through all enabled channels
        
        Args:
            message: Alert message
            level: Alert severity level
            data: Additional data to include
            silent: Suppress Telegram notification sound
            
        Returns:
            True if alert sent successfully
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Format full message
        full_message = f"{level.value} {message}"
        
        if data:
            full_message += "\n\n📊 Details:"
            for key, value in data.items():
                full_message += f"\n  • {key}: {value}"
        
        full_message += f"\n\n🕐 {timestamp}"
        
        # Console logging
        self._log_to_console(message, level, data)
        
        # Telegram notification
        success = True
        if self.telegram_enabled:
            success = self._send_telegram(full_message, silent)
        
        # Update tracking
        self.alert_count += 1
        self.last_alert_time = datetime.now()
        
        return success
    
    def _log_to_console(self, message: str, level: AlertLevel, data: Optional[Dict] = None):
        """Log alert to console"""
        log_msg = f"{level.value} {message}"
        
        if level in [AlertLevel.ERROR, AlertLevel.LOSS]:
            logger.error(log_msg)
        elif level == AlertLevel.WARNING:
            logger.warning(log_msg)
        else:
            logger.info(log_msg)
        
        if data:
            logger.info(f"Details: {data}")
    
    def _send_telegram(self, message: str, silent: bool = False) -> bool:
        """Send message via Telegram"""
        try:
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            payload = {
                "chat_id": self.telegram_chat_id,
                "text": message,
                "parse_mode": "HTML",
                "disable_notification": silent
            }
            
            response = requests.post(url, json=payload, timeout=5)
            
            if response.status_code == 200:
                return True
            else:
                logger.error(f"Telegram API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")
            return False
    
    # Convenience methods for common alerts
    
    def entry_signal(self, strike: str, option_type: str, bias: str, price: float, greeks: Dict):
        """Alert for entry signal"""
        data = {
            "Strike": strike,
            "Type": option_type,
            "Bias": bias,
            "Entry Price": f"₹{price:.2f}",
            "Delta": f"{greeks.get('delta', 0):.3f}",
            "Gamma": f"{greeks.get('gamma', 0):.5f}",
            "IV": f"{greeks.get('iv', 0)*100:.1f}%"
        }
        
        message = f"<b>🎯 ENTRY SIGNAL</b>\n{strike} {option_type} @ ₹{price:.2f}"
        return self.send_alert(message, AlertLevel.TRADE, data)
    
    def trade_executed(self, strike: str, option_type: str, action: str, quantity: int, price: float):
        """Alert for executed trade"""
        data = {
            "Action": action.upper(),
            "Quantity": quantity,
            "Price": f"₹{price:.2f}",
            "Value": f"₹{quantity * price:.2f}"
        }
        
        message = f"<b>✅ TRADE EXECUTED</b>\n{action.upper()} {quantity} x {strike} {option_type}"
        return self.send_alert(message, AlertLevel.SUCCESS, data)
    
    def stop_loss_hit(self, strike: str, option_type: str, entry_price: float, exit_price: float, pnl: float):
        """Alert for stop loss"""
        data = {
            "Entry": f"₹{entry_price:.2f}",
            "Exit": f"₹{exit_price:.2f}",
            "Loss": f"₹{abs(pnl):.2f}",
            "Loss %": f"{(pnl/entry_price)*100:.1f}%"
        }
        
        message = f"<b>🛑 STOP LOSS HIT</b>\n{strike} {option_type}"
        return self.send_alert(message, AlertLevel.LOSS, data)
    
    def target_achieved(self, strike: str, option_type: str, entry_price: float, exit_price: float, pnl: float):
        """Alert for target achieved"""
        data = {
            "Entry": f"₹{entry_price:.2f}",
            "Exit": f"₹{exit_price:.2f}",
            "Profit": f"₹{pnl:.2f}",
            "Profit %": f"{(pnl/entry_price)*100:.1f}%"
        }
        
        message = f"<b>🎯 TARGET ACHIEVED</b>\n{strike} {option_type}"
        return self.send_alert(message, AlertLevel.PROFIT, data)
    
    def position_update(self, positions: int, total_pnl: float, realized_pnl: float, unrealized_pnl: float):
        """Alert for position summary"""
        data = {
            "Open Positions": positions,
            "Total PnL": f"₹{total_pnl:.2f}",
            "Realized": f"₹{realized_pnl:.2f}",
            "Unrealized": f"₹{unrealized_pnl:.2f}"
        }
        
        level = AlertLevel.PROFIT if total_pnl >= 0 else AlertLevel.LOSS
        message = "<b>📊 POSITION UPDATE</b>"
        return self.send_alert(message, level, data, silent=True)
    
    def daily_summary(self, trades: int, wins: int, losses: int, pnl: float, win_rate: float):
        """Alert for daily summary"""
        data = {
            "Total Trades": trades,
            "Wins": wins,
            "Losses": losses,
            "Win Rate": f"{win_rate:.1f}%",
            "Net PnL": f"₹{pnl:.2f}"
        }
        
        level = AlertLevel.PROFIT if pnl >= 0 else AlertLevel.LOSS
        message = "<b>📈 DAILY SUMMARY</b>"
        return self.send_alert(message, level, data)
    
    def risk_alert(self, alert_type: str, current_value: float, threshold: float, action: str):
        """Alert for risk threshold breach"""
        data = {
            "Alert Type": alert_type,
            "Current Value": f"{current_value:.2f}",
            "Threshold": f"{threshold:.2f}",
            "Action Taken": action
        }
        
        message = f"<b>⚠️ RISK ALERT: {alert_type}</b>"
        return self.send_alert(message, AlertLevel.WARNING, data)
    
    def system_event(self, event: str, status: str, details: Optional[str] = None):
        """Alert for system events"""
        data = {
            "Event": event,
            "Status": status
        }
        if details:
            data["Details"] = details
        
        level = AlertLevel.SUCCESS if status == "OK" else AlertLevel.WARNING
        message = f"<b>🔧 SYSTEM EVENT</b>"
        return self.send_alert(message, level, data, silent=True)
    
    def greeks_threshold_breach(self, greek_type: str, current: float, threshold: float, position: str):
        """Alert for Greeks threshold breach"""
        data = {
            "Greek Type": greek_type,
            "Current Value": f"{current:.4f}",
            "Threshold": f"{threshold:.4f}",
            "Position": position
        }
        
        message = f"<b>📊 GREEKS ALERT: {greek_type}</b>"
        return self.send_alert(message, AlertLevel.WARNING, data)


# Singleton instance
_alert_system = None

def get_alert_system() -> AlertSystem:
    """Get singleton alert system instance"""
    global _alert_system
    if _alert_system is None:
        telegram_enabled = os.getenv("TELEGRAM_ALERTS_ENABLED", "true").lower() == "true"
        _alert_system = AlertSystem(telegram_enabled=telegram_enabled)
    return _alert_system
