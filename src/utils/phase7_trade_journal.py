"""
PHASE 7 — TRADE JOURNAL ENGINE

Capture everything
Learn from every trade
Optimize continuously
Future ML fuel
"""

from datetime import datetime
from typing import List, Optional, Dict, Tuple
from dataclasses import asdict
from src.utils.phase7_exit_models import (
    TradeJournalEntry, TradeContextSnapshot, ExitContextSnapshot,
    Phase7Config
)
import json


class TradeJournalEngine:
    """
    Trade journal recorder and analyzer
    
    Every trade recorded:
    - Entry context (price, Greeks, OI, volume)
    - Exit context (price, Greeks, P&L, duration)
    - Exit reason (signal that triggered)
    - Quality score
    
    Philosophy: "You can't improve what you don't measure"
    """
    
    def __init__(self, config: Optional[Phase7Config] = None):
        self.config = config or Phase7Config()
        self.trades: List[TradeJournalEntry] = []
        self.session_start: datetime = datetime.now()
    
    # ====================================================================
    # STEP 1: RECORD TRADE ENTRY
    # ====================================================================
    
    def create_entry_snapshot(
        self,
        entry_time: datetime,
        entry_price: float,
        option_type: str,  # "CE" or "PE"
        entry_delta: float,
        entry_gamma: float,
        entry_theta: float,
        entry_iv: float,
        ce_oi: int,
        pe_oi: int,
        volume_entry: int,
    ) -> TradeContextSnapshot:
        """
        Create entry context snapshot
        """
        
        return TradeContextSnapshot(
            entry_time=entry_time,
            entry_price=entry_price,
            option_type=option_type,
            strike=entry_price,
            delta_entry=entry_delta,
            gamma_entry=entry_gamma,
            theta_entry=entry_theta,
            iv_entry=entry_iv,
            oi_ce_entry=ce_oi,
            oi_pe_entry=pe_oi,
            volume_entry=volume_entry,
        )
    
    # ====================================================================
    # STEP 2: RECORD TRADE EXIT
    # ====================================================================
    
    def create_exit_snapshot(
        self,
        exit_time: datetime,
        exit_price: float,
        exit_delta: float,
        exit_gamma: float,
        exit_theta: float,
        exit_iv: float,
        exit_reason: str,
        quantity: int,
        ce_oi_exit: int,
        pe_oi_exit: int,
    ) -> ExitContextSnapshot:
        """
        Create exit context snapshot
        """
        
        return ExitContextSnapshot(
            exit_time=exit_time,
            exit_price=exit_price,
            exit_reason=exit_reason,
            delta_exit=exit_delta,
            gamma_exit=exit_gamma,
            theta_exit=exit_theta,
            iv_exit=exit_iv,
            oi_ce_exit=ce_oi_exit,
            oi_pe_exit=pe_oi_exit,
            volume_exit=quantity,
        )
    
    # ====================================================================
    # STEP 3: COMPLETE TRADE RECORD
    # ====================================================================
    
    def record_trade(
        self,
        entry_snapshot: TradeContextSnapshot,
        exit_snapshot: ExitContextSnapshot,
        exit_trigger: str,  # e.g., "TRAILING_SL", "PARTIAL_EXIT", "THETA_BOMB"
        position_quantity: int,
    ) -> TradeJournalEntry:
        """
        Record complete trade (entry + exit + analysis)
        """
        
        # Calculate P&L
        duration = (exit_snapshot.exit_time - entry_snapshot.entry_time).total_seconds()
        
        if entry_snapshot.option_type == "CE":
            pnl = (exit_snapshot.exit_price - entry_snapshot.entry_price) * position_quantity
        else:  # PE
            pnl = (entry_snapshot.entry_price - exit_snapshot.exit_price) * position_quantity
        
        pnl_percent = (pnl / (entry_snapshot.entry_price * position_quantity)) * 100 \
                      if entry_snapshot.entry_price != 0 else 0
        
        trade_id = f"T{len(self.trades) + 1}"

        entry = TradeJournalEntry(
            trade_id=trade_id,
            entry_context=entry_snapshot,
            exit_context=exit_snapshot,
            entry_price=entry_snapshot.entry_price,
            exit_price=exit_snapshot.exit_price,
            pnl_rupees=pnl,
            pnl_percent=pnl_percent,
            duration_seconds=int(duration),
        )
        
        # Add to history
        self.trades.append(entry)
        
        return entry
    
    # ====================================================================
    # STEP 4: TRADE QUALITY ANALYSIS
    # ====================================================================
    
    def calculate_trade_quality(self, trade: TradeJournalEntry) -> Tuple[float, str]:
        """
        Score trade quality (0-100)
        
        Factors:
        - Profit: Max 30 points
        - Speed: Max 20 points (fast scalp = good)
        - Risk management: Max 20 points (gamma managed)
        - Execution: Max 20 points (delta, IV conditions)
        - Timing: Max 10 points
        """
        
        score = 0.0
        details = []
        
        # Profit score (max 30)
        if trade.pnl_percent > 1.0:
            score += 30
            details.append("Profit: Excellent (>1%)")
        elif trade.pnl_percent > 0.5:
            score += 20
            details.append("Profit: Good (0.5-1%)")
        elif trade.pnl_percent > 0.2:
            score += 10
            details.append("Profit: OK (0.2-0.5%)")
        elif trade.pnl_percent > 0:
            score += 5
            details.append("Profit: Minimal (<0.2%)")
        else:
            details.append("Profit: Loss")
        
        # Speed score (max 20)
        if trade.duration_seconds < 120:  # <2 mins = scalp
            score += 20
            details.append("Speed: Fast scalp (<2m)")
        elif trade.duration_seconds < 300:  # <5 mins
            score += 15
            details.append("Speed: Good (<5m)")
        elif trade.duration_seconds < 600:  # <10 mins
            score += 10
            details.append("Speed: OK (<10m)")
        else:
            score += 5
            details.append(f"Speed: Long hold ({trade.duration_seconds/60:.0f}m)")
        
        # Risk management score (max 20)
        entry_gamma = trade.entry_greeks.get("gamma", 0)
        exit_gamma = trade.exit_greeks.get("gamma", 0)
        
        if entry_gamma > 0.01:
            score += 10
            details.append("Gamma entry: Good (high)")
        elif entry_gamma > 0.005:
            score += 5
            details.append("Gamma entry: OK")
        
        if exit_gamma < entry_gamma:
            score += 10
            details.append("Gamma exit: Controlled (lower)")
        
        # IV management (max 10)
        iv_diff = ((trade.exit_iv - trade.entry_iv) / trade.entry_iv) * 100 \
                  if trade.entry_iv != 0 else 0
        
        if iv_diff < 0:
            score += 10
            details.append(f"IV: Crushed {abs(iv_diff):.1f}% (profit friendly)")
        elif iv_diff < 5:
            score += 5
            details.append(f"IV: Stable {iv_diff:.1f}%")
        
        return min(100, score), " | ".join(details)
    
    # ====================================================================
    # STEP 5: SESSION STATS
    # ====================================================================
    
    def get_session_stats(self) -> Dict[str, any]:
        """
        Get session-level statistics
        """
        
        if not self.trades:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "total_pnl": 0,
                "avg_pnl_per_trade": 0,
                "max_profit_trade": 0,
                "max_loss_trade": 0,
                "avg_holding_time": 0,
                "exit_signal_breakdown": {},
            }
        
        winning = [t for t in self.trades if t.pnl_rupees > 0]
        losing = [t for t in self.trades if t.pnl_rupees <= 0]
        
        total_pnl = sum(t.pnl_rupees for t in self.trades)
        avg_time = sum(t.duration_seconds for t in self.trades) / len(self.trades) \
                   if self.trades else 0
        
        # Signal breakdown
        signal_breakdown = {}
        for trade in self.trades:
            signal = trade.exit_trigger
            if signal not in signal_breakdown:
                signal_breakdown[signal] = {"count": 0, "pnl": 0}
            signal_breakdown[signal]["count"] += 1
            signal_breakdown[signal]["pnl"] += trade.pnl_rupees
        
        return {
            "total_trades": len(self.trades),
            "winning_trades": len(winning),
            "losing_trades": len(losing),
            "win_rate": (len(winning) / len(self.trades) * 100) if self.trades else 0,
            "total_pnl": total_pnl,
            "avg_pnl_per_trade": total_pnl / len(self.trades) if self.trades else 0,
            "max_profit": max([t.pnl_rupees for t in winning]) if winning else 0,
            "max_loss": min([t.pnl_rupees for t in losing]) if losing else 0,
            "avg_holding_time_secs": avg_time,
            "avg_holding_time_formatted": f"{int(avg_time / 60)}m {int(avg_time % 60)}s",
            "exit_signal_breakdown": signal_breakdown,
        }
    
    def print_session_summary(self) -> str:
        """
        Print formatted session summary
        """
        
        stats = self.get_session_stats()
        
        summary = f"""
╔═══════════════════════════════════════════════════════════════╗
║            PHASE 7 — TRADE JOURNAL SESSION SUMMARY             ║
╚═══════════════════════════════════════════════════════════════╝

📊 PERFORMANCE:
  • Total trades: {stats['total_trades']}
  • Winning trades: {stats['winning_trades']}
  • Losing trades: {stats['losing_trades']}
  • Win rate: {stats['win_rate']:.1f}%
  
💰 P&L:
  • Total P&L: ₹{stats['total_pnl']:,.0f}
  • Avg per trade: ₹{stats['avg_pnl_per_trade']:,.0f}
  • Max win: ₹{stats['max_profit']:,.0f}
  • Max loss: ₹{stats['max_loss']:,.0f}
  
⏱️ TIMING:
  • Avg holding: {stats['avg_holding_time_formatted']}
  
🎯 EXIT SIGNALS:
"""
        
        for signal, data in stats['exit_signal_breakdown'].items():
            signal_pnl = data['pnl']
            signal_count = data['count']
            avg_per_signal = signal_pnl / signal_count if signal_count > 0 else 0
            summary += f"  • {signal}: {signal_count} trades, ₹{signal_pnl:,.0f} total (₹{avg_per_signal:,.0f} avg)\n"
        
        summary += f"\n{'═' * 63}\n"
        
        return summary
    
    # ====================================================================
    # STEP 6: EXPORT & PERSISTENCE
    # ====================================================================
    
    def export_trades_json(self, filepath: str) -> str:
        """
        Export trades to JSON for analysis/ML
        """
        
        trades_data = []
        for trade in self.trades:
            trades_data.append(asdict(trade))
        
        with open(filepath, 'w') as f:
            json.dump(trades_data, f, indent=2, default=str)
        
        return f"Exported {len(self.trades)} trades to {filepath}"
    
    def export_session_report(self, filepath: str) -> str:
        """
        Export session report with stats
        """
        
        report = self.print_session_summary()
        
        with open(filepath, 'w') as f:
            f.write(report)
            f.write("\n\nDETAILED TRADE LIST:\n")
            f.write("=" * 80 + "\n\n")
            
            for i, trade in enumerate(self.trades, 1):
                f.write(f"Trade #{i}\n")
                f.write(f"  Contract: {trade.contract_symbol} {trade.option_type}\n")
                f.write(f"  Entry: ₹{trade.entry_price:.2f} @ {trade.entry_time}\n")
                f.write(f"  Exit: ₹{trade.exit_price:.2f} @ {trade.exit_time}\n")
                f.write(f"  P&L: ₹{trade.pnl_rupees:.0f} ({trade.pnl_percent:+.2f}%)\n")
                f.write(f"  Duration: {trade.duration_seconds}s\n")
                f.write(f"  Exit Signal: {trade.exit_trigger}\n")
                f.write(f"  Reason: {trade.exit_reason}\n")
                f.write(f"  Quality: {self.calculate_trade_quality(trade)[1]}\n")
                f.write("-" * 80 + "\n")
        
        return f"Session report exported to {filepath}"
