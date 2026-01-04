"""
PHASE 9 Dashboard Demo
Shows both Live Dashboard and Post-Trade Analytics in action
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.dashboard.dashboard_aggregator import DashboardAggregator, DashboardDataFeeder
import time


def demo_live_dashboard():
    """Demonstrate Live Dashboard"""
    print("\n" + "="*100)
    print("🎯 PHASE 9 - LIVE DASHBOARD DEMONSTRATION")
    print("="*100)
    
    # Initialize aggregator
    aggregator = DashboardAggregator()
    
    # Load sample data
    print("\n📊 Loading market data...")
    market_data = DashboardDataFeeder.get_sample_market_data()
    option_chain = DashboardDataFeeder.get_sample_option_chain()
    position = DashboardDataFeeder.get_sample_position()
    
    aggregator.update_market_data(market_data)
    aggregator.update_option_chain(option_chain)
    aggregator.update_active_position(position)
    
    # Refresh dashboard
    print("🔄 Refreshing live dashboard...")
    aggregator.refresh_live_dashboard()
    
    # Render terminal dashboard
    dashboard_output = aggregator.render_live_dashboard()
    print(dashboard_output)
    
    # Check alerts
    has_alerts, alerts = aggregator.check_alerts()
    if has_alerts:
        print("\n🚨 ALERTS:")
        for alert in alerts:
            print(f"   {alert}")
    else:
        print("\n✅ No alerts - system healthy")
    
    # Save snapshot
    snapshot_file = "logs/dashboard_snapshot.json"
    Path("logs").mkdir(exist_ok=True)
    aggregator.save_live_snapshot(snapshot_file)
    print(f"\n💾 Dashboard snapshot saved to: {snapshot_file}")
    
    return aggregator


def demo_post_trade_analytics(aggregator: DashboardAggregator):
    """Demonstrate Post-Trade Analytics"""
    print("\n\n" + "="*100)
    print("📈 PHASE 9 - POST-TRADE ANALYTICS DEMONSTRATION")
    print("="*100)
    
    # Load completed trades
    print("\n📂 Loading completed trades...")
    trades = DashboardDataFeeder.get_sample_completed_trades()
    aggregator.load_completed_trades(trades)
    print(f"   Loaded {len(trades)} trades for analysis")
    
    # Run analytics
    print("\n🔬 Running comprehensive analytics...")
    time.sleep(1)  # Simulate processing
    
    report = aggregator.run_post_trade_analysis(period="WEEK")
    print(report)
    
    # Save report
    report_file = "logs/post_trade_analytics.txt"
    aggregator.save_analytics_report(report_file)
    print(f"\n💾 Analytics report saved to: {report_file}")


def demo_dashboard_data_extraction():
    """Show how to extract specific data from dashboard"""
    print("\n\n" + "="*100)
    print("🔍 DASHBOARD DATA EXTRACTION")
    print("="*100)
    
    aggregator = DashboardAggregator()
    
    # Setup data
    aggregator.update_market_data(DashboardDataFeeder.get_sample_market_data())
    aggregator.update_option_chain(DashboardDataFeeder.get_sample_option_chain())
    aggregator.update_active_position(DashboardDataFeeder.get_sample_position())
    aggregator.refresh_live_dashboard()
    
    # Extract specific components
    print("\n📊 Market Overview:")
    if aggregator.live_dashboard.market_overview:
        overview = aggregator.live_dashboard.market_overview
        print(f"   NIFTY Spot: {overview.nifty_spot:.2f}")
        print(f"   Change: {overview.spot_change_pct:+.2f}%")
        print(f"   Status: {overview.market_status.value}")
    
    print("\n📈 Bias Panel:")
    if aggregator.live_dashboard.bias_panel:
        bias = aggregator.live_dashboard.bias_panel
        print(f"   Bias: {bias.market_bias}")
        print(f"   Strength: {bias.bias_strength:.2f} ({bias.get_bias_grade()})")
        print(f"   Trade Allowed: {bias.trade_allowed.value}")
    
    print("\n💼 Position:")
    if aggregator.live_dashboard.trade_monitor:
        monitor = aggregator.live_dashboard.trade_monitor
        if monitor.has_position:
            print(f"   Symbol: {monitor.symbol} {monitor.strike} {monitor.option_type}")
            print(f"   Entry: ₹{monitor.entry_price:.2f}")
            print(f"   Current: ₹{monitor.current_price:.2f}")
            print(f"   PnL: ₹{monitor.unrealized_pnl:+.2f} ({monitor.pnl_percentage:+.2f}%)")
        else:
            print("   No active position")
    
    print("\n🛡️ Risk Status:")
    if aggregator.live_dashboard.risk_panel:
        risk = aggregator.live_dashboard.risk_panel
        print(f"   Trades Today: {risk.trades_taken_today}/{risk.max_trades_allowed}")
        print(f"   Daily PnL: ₹{risk.daily_pnl:+,.2f}")
        print(f"   Status: {risk.get_safety_status()}")
        print(f"   Consecutive Wins/Losses: {risk.consecutive_wins}/{risk.consecutive_losses}")
    
    print("\n🎯 Option Chain Intelligence:")
    if aggregator.live_dashboard.option_chain:
        chain = aggregator.live_dashboard.option_chain
        dominant = chain.get_dominant_strikes()
        buildup = chain.get_max_oi_buildup()
        
        print(f"   ATM Strike: {chain.atm_strike}")
        print(f"   CE Dominant Strikes: {dominant['ce_dominant_strikes']}")
        print(f"   PE Dominant Strikes: {dominant['pe_dominant_strikes']}")
        
        if buildup:
            print(f"\n   Max CE Buildup: {buildup['max_ce_buildup']['strike']} "
                  f"(Δ OI: {buildup['max_ce_buildup']['oi_delta']:+,})")
            print(f"   Max PE Buildup: {buildup['max_pe_buildup']['strike']} "
                  f"(Δ OI: {buildup['max_pe_buildup']['oi_delta']:+,})")


def run_complete_demo():
    """Run complete dashboard demonstration"""
    print("\n" + "#"*100)
    print("#" + " "*98 + "#")
    print("#" + " "*30 + "ANGEL-X PHASE 9 DASHBOARD" + " "*43 + "#")
    print("#" + " "*30 + "COMMAND CENTER DEMO" + " "*49 + "#")
    print("#" + " "*98 + "#")
    print("#"*100)
    
    # Part A: Live Dashboard
    aggregator = demo_live_dashboard()
    
    input("\n\nPress Enter to continue to Post-Trade Analytics...")
    
    # Part B: Post-Trade Analytics
    demo_post_trade_analytics(aggregator)
    
    input("\n\nPress Enter to see data extraction examples...")
    
    # Data Extraction Examples
    demo_dashboard_data_extraction()
    
    # Final summary
    print("\n\n" + "="*100)
    print("✅ PHASE 9 DEMONSTRATION COMPLETE")
    print("="*100)
    print("""
Dashboard Components Demonstrated:

LIVE DASHBOARD (Part A):
  ✅ Market Overview Panel
  ✅ Option Chain Intelligence View
  ✅ Bias & Eligibility Panel
  ✅ Live Trade Monitor
  ✅ Risk & Safety Panel

POST-TRADE ANALYTICS (Part B):
  ✅ PnL Analytics
  ✅ Exit Reason Analysis
  ✅ Greeks Accuracy Report
  ✅ OI + Volume Conviction Report
  ✅ Time-of-Day Performance

FEATURES:
  ✅ Real-time monitoring
  ✅ Alert system
  ✅ Data extraction
  ✅ JSON snapshots
  ✅ Comprehensive reports

FILES CREATED:
  📄 logs/dashboard_snapshot.json
  📄 logs/post_trade_analytics.txt

NEXT STEPS:
  1. Integrate with live Angel One data feed
  2. Connect to Phase 1-8 trading engines
  3. Add web UI (Flask/FastAPI) for browser access
  4. Set up automated daily reports
  5. Configure real-time alerts (Telegram/Email)
""")
    
    print("="*100 + "\n")


if __name__ == "__main__":
    try:
        run_complete_demo()
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
