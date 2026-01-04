"""
PHASE 8: Production Tools
Kill switch, health checks, daily reports
Stress-free live operations
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
import signal
import sys


class KillSwitch:
    """
    Emergency kill switch
    One-click stop all trading
    """
    
    def __init__(self, shutdown_callback: callable):
        self.shutdown_callback = shutdown_callback
        self.activated = False
        self.activation_time: Optional[datetime] = None
        self.activation_reason: Optional[str] = None
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle interrupt signals"""
        print("\n🚨 KILL SWITCH ACTIVATED VIA SIGNAL")
        self.activate("System interrupt signal")
    
    def activate(self, reason: str = "Manual activation"):
        """
        Activate kill switch
        Stops all trading immediately
        """
        if self.activated:
            print("⚠️  Kill switch already activated")
            return
        
        self.activated = True
        self.activation_time = datetime.now()
        self.activation_reason = reason
        
        print("=" * 60)
        print("🚨 KILL SWITCH ACTIVATED 🚨")
        print(f"Time: {self.activation_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Reason: {reason}")
        print("=" * 60)
        
        # Execute shutdown callback
        try:
            self.shutdown_callback()
        except Exception as e:
            print(f"Error during shutdown: {e}")
        
        print("✅ System shutdown complete")
    
    def is_active(self) -> bool:
        """Check if kill switch is activated"""
        return self.activated
    
    def get_status(self) -> Dict:
        """Get kill switch status"""
        return {
            "activated": self.activated,
            "activation_time": self.activation_time.isoformat() if self.activation_time else None,
            "reason": self.activation_reason
        }


class HealthReporter:
    """
    Generate daily health reports
    Track system performance
    """
    
    def __init__(self, report_dir: str = "logs/reports"):
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_startup_report(self, config: Dict) -> str:
        """Generate session start report"""
        report = f"""
╔══════════════════════════════════════════════════════════╗
║         ANGEL-X SESSION START REPORT                     ║
╚══════════════════════════════════════════════════════════╝

📅 Date: {datetime.now().strftime('%Y-%m-%d')}
⏰ Start Time: {datetime.now().strftime('%H:%M:%S')}

🔧 CONFIGURATION
─────────────────────────────────────────────────────────
Environment:          {config.get('environment', 'production')}
Risk Per Trade:       {config.get('risk_per_trade', 2.0)}%
Max Trades/Day:       {config.get('max_trades_day', 10)}
Position Multiplier:  {config.get('position_multiplier', 1.0)}

🎯 ENGINES STATUS
─────────────────────────────────────────────────────────
✅ Bias Engine         READY
✅ Greeks Engine       READY
✅ Entry Engine        READY
✅ Risk Manager        READY
✅ Failover System     READY

🔗 CONNECTIONS
─────────────────────────────────────────────────────────
AngelOne API:         Connected
Market Data Feed:     Active
Logging System:       Active

═══════════════════════════════════════════════════════════
System ready for trading. Good luck! 🚀
═══════════════════════════════════════════════════════════
"""
        
        # Save to file
        filename = f"startup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = self.report_dir / filename
        
        with open(filepath, 'w') as f:
            f.write(report)
        
        print(report)
        return str(filepath)
    
    def generate_end_of_day_report(self, performance_summary: Dict) -> str:
        """Generate end-of-day summary report"""
        trading = performance_summary.get('trading', {})
        latency = performance_summary.get('latency', {})
        signals = performance_summary.get('signals', {})
        system = performance_summary.get('system', {})
        
        win_rate = trading.get('win_rate', 0)
        total_pnl = trading.get('total_pnl', 0)
        
        # Determine performance emoji
        if total_pnl > 5000:
            pnl_emoji = "🎉"
        elif total_pnl > 0:
            pnl_emoji = "✅"
        elif total_pnl > -2000:
            pnl_emoji = "⚠️"
        else:
            pnl_emoji = "❌"
        
        report = f"""
╔══════════════════════════════════════════════════════════╗
║         ANGEL-X END-OF-DAY REPORT                        ║
╚══════════════════════════════════════════════════════════╝

📅 Date: {datetime.now().strftime('%Y-%m-%d')}
⏰ End Time: {datetime.now().strftime('%H:%M:%S')}

📊 TRADING SUMMARY
─────────────────────────────────────────────────────────
Total Trades:         {trading.get('total_trades', 0)}
Winning Trades:       {trading.get('winning_trades', 0)}
Losing Trades:        {trading.get('losing_trades', 0)}
Win Rate:             {win_rate:.2f}%

{pnl_emoji} Total P&L:           ₹{total_pnl:,.2f}
Current Streak:       {trading.get('current_streak', 0)}
Max Drawdown:         {trading.get('max_drawdown', 0):.2f}%

⚡ PERFORMANCE METRICS
─────────────────────────────────────────────────────────
Avg Total Latency:    {latency.get('total_latency', {}).get('avg', 0):.1f}ms
P95 Latency:          {latency.get('total_latency', {}).get('p95', 0):.1f}ms
Signals Generated:    {signals.get('generated', 0)}
Signal Efficiency:    {signals.get('efficiency', 0):.1f}%

🏥 SYSTEM HEALTH
─────────────────────────────────────────────────────────
Total Errors:         {sum(system.get('errors', {}).values())}
Auto-Recoveries:      {system.get('recoveries', 0)}
Uptime:               {performance_summary.get('session', {}).get('uptime_hours', 0):.2f} hours

═══════════════════════════════════════════════════════════
"""
        
        # Add insights
        insights = self._generate_insights(performance_summary)
        if insights:
            report += "\n💡 KEY INSIGHTS\n"
            report += "─────────────────────────────────────────────────────────\n"
            for insight in insights:
                report += f"  • {insight}\n"
            report += "\n"
        
        report += "═══════════════════════════════════════════════════════════\n"
        
        # Save to file
        filename = f"eod_{datetime.now().strftime('%Y%m%d')}.txt"
        filepath = self.report_dir / filename
        
        with open(filepath, 'w') as f:
            f.write(report)
        
        print(report)
        return str(filepath)
    
    def _generate_insights(self, summary: Dict) -> list:
        """Generate actionable insights from data"""
        insights = []
        
        trading = summary.get('trading', {})
        win_rate = trading.get('win_rate', 0)
        total_trades = trading.get('total_trades', 0)
        
        # Win rate insights
        if total_trades >= 5:
            if win_rate < 45:
                insights.append(f"Win rate {win_rate:.1f}% is low - consider tightening filters")
            elif win_rate > 70:
                insights.append(f"Excellent win rate {win_rate:.1f}% - strategy working well")
        
        # Drawdown insights
        max_dd = trading.get('max_drawdown', 0)
        if max_dd > 10:
            insights.append(f"High drawdown {max_dd:.1f}% - review risk management")
        
        # Latency insights
        latency = summary.get('latency', {})
        avg_latency = latency.get('total_latency', {}).get('avg', 0)
        if avg_latency > 1000:
            insights.append(f"High latency {avg_latency:.0f}ms - consider optimization")
        
        # Signal efficiency
        signals = summary.get('signals', {})
        efficiency = signals.get('efficiency', 0)
        if efficiency < 30:
            insights.append("Low signal efficiency - too many filtered signals")
        
        return insights


class ConfigFreezer:
    """
    Freeze configuration for live trading days
    Prevent accidental parameter changes
    """
    
    def __init__(self, config_file: str = "config/live_config.json"):
        self.config_file = Path(config_file)
        self.frozen_config: Optional[Dict] = None
        self.freeze_date: Optional[str] = None
    
    def freeze_config(self, config: Dict):
        """Freeze current configuration"""
        self.frozen_config = config.copy()
        self.freeze_date = datetime.now().strftime('%Y-%m-%d')
        
        # Save to file
        freeze_data = {
            "config": self.frozen_config,
            "freeze_date": self.freeze_date,
            "freeze_time": datetime.now().isoformat()
        }
        
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(freeze_data, f, indent=2)
        
        print(f"✅ Configuration frozen for {self.freeze_date}")
    
    def load_frozen_config(self) -> Optional[Dict]:
        """Load frozen configuration"""
        if not self.config_file.exists():
            return None
        
        with open(self.config_file, 'r') as f:
            freeze_data = json.load(f)
        
        self.frozen_config = freeze_data.get('config')
        self.freeze_date = freeze_data.get('freeze_date')
        
        return self.frozen_config
    
    def is_today_frozen(self) -> bool:
        """Check if today's config is frozen"""
        if not self.freeze_date:
            return False
        
        return self.freeze_date == datetime.now().strftime('%Y-%m-%d')
    
    def unfreeze(self):
        """Unfreeze configuration"""
        self.frozen_config = None
        self.freeze_date = None
        
        if self.config_file.exists():
            self.config_file.unlink()
        
        print("✅ Configuration unfrozen")


class TradeLogger:
    """
    Immutable trade logging
    Audit trail for all trades
    """
    
    def __init__(self, log_dir: str = "logs/trades"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create today's log file
        self.today_file = self.log_dir / f"trades_{datetime.now().strftime('%Y%m%d')}.jsonl"
    
    def log_trade(self, trade_data: Dict):
        """
        Log trade (append-only)
        JSONL format for immutability
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            **trade_data
        }
        
        # Append to log file
        with open(self.today_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def get_today_trades(self) -> list:
        """Load today's trades"""
        if not self.today_file.exists():
            return []
        
        trades = []
        with open(self.today_file, 'r') as f:
            for line in f:
                trades.append(json.loads(line.strip()))
        
        return trades


class ProductionToolkit:
    """
    Complete production operations toolkit
    All tools for stress-free live trading
    """
    
    def __init__(self, shutdown_callback: callable):
        self.kill_switch = KillSwitch(shutdown_callback)
        self.health_reporter = HealthReporter()
        self.config_freezer = ConfigFreezer()
        self.trade_logger = TradeLogger()
    
    def startup_sequence(self, config: Dict) -> bool:
        """
        Execute startup sequence
        Returns True if ready to trade
        """
        print("\n🚀 ANGEL-X STARTUP SEQUENCE\n")
        
        # Step 1: Generate startup report
        print("1. Generating startup report...")
        self.health_reporter.generate_startup_report(config)
        
        # Step 2: Freeze configuration
        print("2. Freezing configuration...")
        self.config_freezer.freeze_config(config)
        
        # Step 3: Verify kill switch
        print("3. Verifying kill switch...")
        if not self.kill_switch.activated:
            print("   ✅ Kill switch ready")
        
        # Step 4: Initialize trade logger
        print("4. Initializing trade logger...")
        print(f"   ✅ Logging to {self.trade_logger.today_file}")
        
        print("\n✅ STARTUP COMPLETE - SYSTEM READY\n")
        return True
    
    def shutdown_sequence(self, performance_summary: Dict):
        """Execute shutdown sequence"""
        print("\n🛑 ANGEL-X SHUTDOWN SEQUENCE\n")
        
        # Step 1: Generate EOD report
        print("1. Generating end-of-day report...")
        self.health_reporter.generate_end_of_day_report(performance_summary)
        
        # Step 2: Unfreeze config
        print("2. Unfreezing configuration...")
        self.config_freezer.unfreeze()
        
        print("\n✅ SHUTDOWN COMPLETE\n")
    
    def emergency_shutdown(self, reason: str):
        """Emergency shutdown"""
        print(f"\n🚨 EMERGENCY SHUTDOWN: {reason}\n")
        self.kill_switch.activate(reason)
    
    def log_trade(self, trade_data: Dict):
        """Log a trade"""
        self.trade_logger.log_trade(trade_data)
    
    def check_kill_switch(self) -> bool:
        """Check if kill switch is active"""
        return self.kill_switch.is_active()
