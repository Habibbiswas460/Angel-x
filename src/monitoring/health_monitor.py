"""
Monitoring and Alerting System
Real-time health monitoring with Telegram notifications
"""

from typing import Optional, Dict, Callable
from dataclasses import dataclass
from datetime import datetime
import logging
import asyncio
import requests

logger = logging.getLogger(__name__)


@dataclass
class AlertConfig:
    """Alert configuration"""

    telegram_bot_token: str
    telegram_chat_id: str
    enable_alerts: bool = True
    alert_levels: Dict[str, bool] = None  # {'critical': True, 'warning': True, 'info': False}

    def __post_init__(self):
        if self.alert_levels is None:
            self.alert_levels = {"critical": True, "warning": True, "info": False}


@dataclass
class HealthMetric:
    """Health metric snapshot"""

    timestamp: datetime
    broker_connected: bool
    database_healthy: bool
    api_responding: bool
    memory_usage_mb: float
    cpu_percent: float
    model_trained: bool
    error_count: int = 0


class TelegramAlerter:
    """Send alerts via Telegram"""

    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    def send(self, message: str, level: str = "info") -> bool:
        """Send Telegram message"""
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram config missing—alerts disabled")
            return False

        # Emoji by level
        emoji = {"critical": "🚨", "warning": "⚠️", "info": "ℹ️"}
        prefix = emoji.get(level, "")

        formatted = f"{prefix} **{level.upper()}** [{datetime.now().strftime('%H:%M:%S')}]\n{message}"

        try:
            response = requests.post(
                self.api_url, json={"chat_id": self.chat_id, "text": formatted, "parse_mode": "MarkdownV2"}, timeout=5
            )
            if response.status_code == 200:
                logger.info(f"Telegram alert sent ({level})")
                return True
        except Exception as e:
            logger.error(f"Telegram send failed: {e}")

        return False


class HealthMonitor:
    """Monitor system health"""

    def __init__(self, alert_config: Optional[AlertConfig] = None):
        self.alert_config = alert_config
        self.alerter = (
            TelegramAlerter(alert_config.telegram_bot_token, alert_config.telegram_chat_id) if alert_config else None
        )

        self.metrics_history = []
        self.alert_thresholds = {"memory_mb": 2000, "cpu_percent": 80, "error_count": 10}

    def check_health(
        self,
        broker_connected: bool,
        database_healthy: bool,
        api_responding: bool,
        memory_usage_mb: float,
        cpu_percent: float,
        model_trained: bool,
        error_count: int = 0,
    ) -> HealthMetric:
        """Check system health and trigger alerts"""

        metric = HealthMetric(
            timestamp=datetime.now(),
            broker_connected=broker_connected,
            database_healthy=database_healthy,
            api_responding=api_responding,
            memory_usage_mb=memory_usage_mb,
            cpu_percent=cpu_percent,
            model_trained=model_trained,
            error_count=error_count,
        )

        self.metrics_history.append(metric)

        # Check thresholds
        alerts = []

        if not broker_connected:
            alerts.append(("critical", "🔌 Broker disconnected"))

        if not database_healthy:
            alerts.append(("critical", "🗄️ Database unhealthy"))

        if not api_responding:
            alerts.append(("critical", "🌐 API not responding"))

        if memory_usage_mb > self.alert_thresholds["memory_mb"]:
            alerts.append(("warning", f"💾 High memory: {memory_usage_mb:.0f}MB"))

        if cpu_percent > self.alert_thresholds["cpu_percent"]:
            alerts.append(("warning", f"⚡ High CPU: {cpu_percent:.1f}%"))

        if error_count > self.alert_thresholds["error_count"]:
            alerts.append(("warning", f"❌ Errors: {error_count}"))

        # Send alerts
        for level, message in alerts:
            if self._should_alert(level):
                self._send_alert(message, level)

        return metric

    def _should_alert(self, level: str) -> bool:
        """Check if alert should be sent"""
        if not self.alert_config:
            return False
        return self.alert_config.alert_levels.get(level, False)

    def _send_alert(self, message: str, level: str):
        """Send alert via configured channels"""
        if self.alerter:
            self.alerter.send(message, level)
        logger.log(logging.WARNING if level == "warning" else logging.ERROR, f"ALERT [{level}]: {message}")

    def get_status_report(self) -> Dict:
        """Get current health status report"""
        if not self.metrics_history:
            return {"status": "no_data"}

        latest = self.metrics_history[-1]
        return {
            "timestamp": latest.timestamp.isoformat(),
            "broker": "connected" if latest.broker_connected else "disconnected",
            "database": "healthy" if latest.database_healthy else "unhealthy",
            "api": "responding" if latest.api_responding else "not_responding",
            "memory_mb": f"{latest.memory_usage_mb:.0f}",
            "cpu_percent": f"{latest.cpu_percent:.1f}",
            "model": "trained" if latest.model_trained else "not_trained",
            "errors": latest.error_count,
        }


class MetricsCollector:
    """Collect system metrics"""

    @staticmethod
    def get_memory_usage() -> float:
        """Get process memory in MB"""
        try:
            import psutil

            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except:
            return 0.0

    @staticmethod
    def get_cpu_percent() -> float:
        """Get process CPU usage"""
        try:
            import psutil

            process = psutil.Process()
            return process.cpu_percent(interval=0.1)
        except:
            return 0.0

    @staticmethod
    def create_dashboard_widget() -> str:
        """Create ASCII dashboard widget"""
        from datetime import datetime

        now = datetime.now()
        return f"""
╔════ ANGEL-X MONITORING ════╗
║ {now.strftime('%Y-%m-%d %H:%M:%S')}
║ Status: 🟢 RUNNING
║ Broker: 🔌 CONNECTED
║ API: 🌐 RESPONDING
║ Memory: 💾 1024MB
║ CPU: ⚡ 15%
╚═══════════════════════════╝
        """.strip()


# Global health monitor
_monitor: Optional[HealthMonitor] = None


def get_monitor(alert_config: Optional[AlertConfig] = None) -> HealthMonitor:
    """Get or create global health monitor"""
    global _monitor
    if _monitor is None:
        _monitor = HealthMonitor(alert_config)
    return _monitor
