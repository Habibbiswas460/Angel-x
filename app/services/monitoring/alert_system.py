"""
Alert and Notification System
Handles trade alerts, system alerts, and risk notifications
Routes alerts to multiple channels: logs, webhooks, email, SMS
"""

import logging
import json
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
import threading
import time

from app.utils.logger import StrategyLogger
from config import config

logger = StrategyLogger.get_logger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AlertType(Enum):
    """Types of alerts"""
    TRADE_ENTRY = "TRADE_ENTRY"
    TRADE_EXIT = "TRADE_EXIT"
    LOSS_LIMIT = "LOSS_LIMIT"
    POSITION_RISK = "POSITION_RISK"
    SYSTEM_ERROR = "SYSTEM_ERROR"
    MARKET_EVENT = "MARKET_EVENT"
    BROKER_DISCONNECT = "BROKER_DISCONNECT"
    CONFIGURATION = "CONFIGURATION"


@dataclass
class Alert:
    """Alert message structure"""
    timestamp: datetime
    severity: AlertSeverity
    alert_type: AlertType
    title: str
    message: str
    details: Dict
    alert_id: str
    

class AlertHandler:
    """Base alert handler"""
    def handle(self, alert: Alert) -> bool:
        raise NotImplementedError


class LogAlertHandler(AlertHandler):
    """Log-based alert handler"""
    def handle(self, alert: Alert) -> bool:
        try:
            if alert.severity == AlertSeverity.CRITICAL:
                logger.critical(f"[{alert.alert_type.value}] {alert.title}: {alert.message}")
            elif alert.severity == AlertSeverity.ERROR:
                logger.error(f"[{alert.alert_type.value}] {alert.title}: {alert.message}")
            elif alert.severity == AlertSeverity.WARNING:
                logger.warning(f"[{alert.alert_type.value}] {alert.title}: {alert.message}")
            else:
                logger.info(f"[{alert.alert_type.value}] {alert.title}: {alert.message}")
            return True
        except Exception as e:
            logger.error(f"LogAlertHandler error: {e}")
            return False


class WebhookAlertHandler(AlertHandler):
    """Webhook-based alert handler for external integrations"""
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.timeout = 5
    
    def handle(self, alert: Alert) -> bool:
        try:
            import requests
            
            payload = {
                "timestamp": alert.timestamp.isoformat(),
                "severity": alert.severity.value,
                "type": alert.alert_type.value,
                "title": alert.title,
                "message": alert.message,
                "details": alert.details,
                "alert_id": alert.alert_id
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code in (200, 201, 202):
                logger.debug(f"Webhook alert sent successfully: {alert.alert_id}")
                return True
            else:
                logger.error(f"Webhook failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"WebhookAlertHandler error: {e}")
            return False


class EmailAlertHandler(AlertHandler):
    """Email alert handler"""
    def __init__(self, smtp_config: Dict):
        self.smtp_config = smtp_config
    
    def handle(self, alert: Alert) -> bool:
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # Extract SMTP configuration
            smtp_server = self.smtp_config.get('server')
            smtp_port = self.smtp_config.get('port', 587)
            sender_email = self.smtp_config.get('sender_email')
            sender_password = self.smtp_config.get('sender_password')
            recipient_email = self.smtp_config.get('recipient_email')
            
            if not all([smtp_server, sender_email, sender_password, recipient_email]):
                logger.warning("Email configuration incomplete - skipping email alert")
                return False
            
            # Create email
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = recipient_email
            msg['Subject'] = f"[ANGEL-X] {alert.severity.value}: {alert.title}"
            
            # Email body
            body = f"""
Alert Type: {alert.alert_type.value}
Severity: {alert.severity.value}
Time: {alert.timestamp}
Title: {alert.title}

Message:
{alert.message}

Details:
{json.dumps(alert.details, indent=2)}

Alert ID: {alert.alert_id}
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)
            
            logger.info(f"Email alert sent: {alert.alert_id}")
            return True
            
        except Exception as e:
            logger.error(f"EmailAlertHandler error: {e}")
            return False


class AlertSystem:
    """
    Central Alert System
    Manages alert routing, handlers, and delivery
    """
    
    def __init__(self):
        """Initialize alert system"""
        self.handlers: List[AlertHandler] = []
        self.alert_queue: List[Alert] = []
        self.alert_lock = threading.Lock()
        
        # Processing thread
        self.running = False
        self.processor_thread: Optional[threading.Thread] = None
        
        # Statistics
        self.alerts_sent = 0
        self.alerts_failed = 0
        
        # Alert history
        self.max_history = 1000
        self.alert_history: List[Alert] = []
        
        # Setup default handlers
        self._setup_default_handlers()
        
        logger.info("AlertSystem initialized")
    
    def _setup_default_handlers(self):
        """Setup default alert handlers"""
        # Always add log handler
        self.add_handler(LogAlertHandler())
        
        # Add webhook if configured
        webhook_url = getattr(config, 'ALERT_WEBHOOK_URL', None)
        if webhook_url:
            try:
                self.add_handler(WebhookAlertHandler(webhook_url))
                logger.info(f"Webhook handler registered: {webhook_url}")
            except Exception as e:
                logger.warning(f"Failed to register webhook handler: {e}")
        
        # Add email if configured
        email_config = getattr(config, 'ALERT_EMAIL_CONFIG', None)
        if email_config:
            try:
                self.add_handler(EmailAlertHandler(email_config))
                logger.info("Email handler registered")
            except Exception as e:
                logger.warning(f"Failed to register email handler: {e}")
    
    def add_handler(self, handler: AlertHandler):
        """Register an alert handler"""
        self.handlers.append(handler)
        logger.debug(f"Alert handler registered: {handler.__class__.__name__}")
    
    def start(self):
        """Start alert processing thread"""
        if self.running:
            return
        
        self.running = True
        self.processor_thread = threading.Thread(
            target=self._process_alerts,
            daemon=True
        )
        self.processor_thread.start()
        logger.info("Alert system processing started")
    
    def stop(self):
        """Stop alert processing"""
        self.running = False
        if self.processor_thread:
            self.processor_thread.join(timeout=5)
        logger.info("Alert system stopped")
    
    def _process_alerts(self):
        """Background thread for alert processing"""
        while self.running:
            try:
                with self.alert_lock:
                    if self.alert_queue:
                        alert = self.alert_queue.pop(0)
                        self._dispatch_alert(alert)
                
                time.sleep(0.1)  # Batch processing
            except Exception as e:
                logger.error(f"Alert processing error: {e}")
    
    def _dispatch_alert(self, alert: Alert):
        """Dispatch alert to all handlers"""
        success_count = 0
        
        for handler in self.handlers:
            try:
                if handler.handle(alert):
                    success_count += 1
                else:
                    self.alerts_failed += 1
            except Exception as e:
                logger.error(f"Handler {handler.__class__.__name__} failed: {e}")
                self.alerts_failed += 1
        
        if success_count > 0:
            self.alerts_sent += 1
        
        # Add to history
        with self.alert_lock:
            self.alert_history.append(alert)
            if len(self.alert_history) > self.max_history:
                self.alert_history = self.alert_history[-self.max_history:]
    
    def send_alert(
        self,
        severity: AlertSeverity,
        alert_type: AlertType,
        title: str,
        message: str,
        details: Optional[Dict] = None,
        sync: bool = False
    ) -> str:
        """
        Send an alert
        
        Args:
            severity: Alert severity level
            alert_type: Type of alert
            title: Alert title
            message: Alert message
            details: Additional details dict
            sync: If True, process immediately; if False, queue for async processing
        
        Returns:
            Alert ID
        """
        alert_id = f"ALT_{int(time.time())}_{len(self.alert_history)}"
        
        alert = Alert(
            timestamp=datetime.now(),
            severity=severity,
            alert_type=alert_type,
            title=title,
            message=message,
            details=details or {},
            alert_id=alert_id
        )
        
        if sync:
            # Process immediately
            self._dispatch_alert(alert)
        else:
            # Queue for async processing
            with self.alert_lock:
                self.alert_queue.append(alert)
        
        return alert_id
    
    def send_trade_entry_alert(self, symbol: str, side: str, qty: int, price: float, **details):
        """Send trade entry alert"""
        return self.send_alert(
            severity=AlertSeverity.INFO,
            alert_type=AlertType.TRADE_ENTRY,
            title=f"Trade Entry: {side} {qty} {symbol}",
            message=f"Entered {side} position on {symbol} @ ₹{price:.2f}",
            details={
                'symbol': symbol,
                'side': side,
                'quantity': qty,
                'entry_price': price,
                **details
            }
        )
    
    def send_trade_exit_alert(self, symbol: str, side: str, qty: int, exit_price: float, pnl: float, **details):
        """Send trade exit alert"""
        severity = AlertSeverity.INFO if pnl > 0 else AlertSeverity.WARNING
        return self.send_alert(
            severity=severity,
            alert_type=AlertType.TRADE_EXIT,
            title=f"Trade Exit: {symbol} ({pnl:+.2f})",
            message=f"Exited {side} {qty} {symbol} @ ₹{exit_price:.2f} | P&L: ₹{pnl:+.2f}",
            details={
                'symbol': symbol,
                'side': side,
                'quantity': qty,
                'exit_price': exit_price,
                'pnl': pnl,
                **details
            }
        )
    
    def send_loss_limit_alert(self, daily_loss: float, loss_limit: float, **details):
        """Send daily loss limit alert"""
        return self.send_alert(
            severity=AlertSeverity.CRITICAL,
            alert_type=AlertType.LOSS_LIMIT,
            title=f"Daily Loss Limit Hit: ₹{daily_loss:.2f}",
            message=f"Daily loss (₹{daily_loss:.2f}) has hit limit (₹{loss_limit:.2f}). Trading halted.",
            details={
                'daily_loss': daily_loss,
                'loss_limit': loss_limit,
                **details
            }
        )
    
    def send_position_risk_alert(self, symbol: str, current_loss: float, max_loss: float, **details):
        """Send position risk alert"""
        return self.send_alert(
            severity=AlertSeverity.WARNING,
            alert_type=AlertType.POSITION_RISK,
            title=f"Position Risk: {symbol}",
            message=f"Current loss (₹{current_loss:.2f}) approaching max loss (₹{max_loss:.2f})",
            details={
                'symbol': symbol,
                'current_loss': current_loss,
                'max_loss': max_loss,
                **details
            }
        )
    
    def send_system_error_alert(self, error: str, **details):
        """Send system error alert"""
        return self.send_alert(
            severity=AlertSeverity.ERROR,
            alert_type=AlertType.SYSTEM_ERROR,
            title="System Error",
            message=error,
            details=details
        )
    
    def send_broker_disconnect_alert(self, reason: str, **details):
        """Send broker disconnect alert"""
        return self.send_alert(
            severity=AlertSeverity.CRITICAL,
            alert_type=AlertType.BROKER_DISCONNECT,
            title="Broker Disconnected",
            message=f"Connection to broker lost: {reason}",
            details={'reason': reason, **details}
        )
    
    def get_history(self, limit: int = 100, alert_type: Optional[AlertType] = None) -> List[Dict]:
        """Get alert history"""
        with self.alert_lock:
            history = self.alert_history[-limit:]
        
        result = []
        for alert in history:
            if alert_type and alert.alert_type != alert_type:
                continue
            
            result.append({
                'alert_id': alert.alert_id,
                'timestamp': alert.timestamp.isoformat(),
                'severity': alert.severity.value,
                'type': alert.alert_type.value,
                'title': alert.title,
                'message': alert.message,
                'details': alert.details
            })
        
        return result
    
    def get_stats(self) -> Dict:
        """Get alert system statistics"""
        return {
            'alerts_sent': self.alerts_sent,
            'alerts_failed': self.alerts_failed,
            'queue_size': len(self.alert_queue),
            'history_size': len(self.alert_history),
            'handlers_count': len(self.handlers)
        }


# Global alert system instance
_alert_system: Optional[AlertSystem] = None


def get_alert_system() -> AlertSystem:
    """Get or create global alert system"""
    global _alert_system
    if _alert_system is None:
        _alert_system = AlertSystem()
        _alert_system.start()
    return _alert_system


__all__ = [
    'AlertSystem',
    'Alert',
    'AlertSeverity',
    'AlertType',
    'AlertHandler',
    'LogAlertHandler',
    'WebhookAlertHandler',
    'EmailAlertHandler',
    'get_alert_system'
]
