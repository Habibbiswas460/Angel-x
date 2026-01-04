"""
PHASE 8.7 & 8.8: Over-Optimization Guard + Live Readiness Checklist
Prevent curve-fitting and ensure production readiness
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
from pathlib import Path


@dataclass
class ParameterChange:
    """Record of parameter modification"""
    parameter_name: str
    old_value: any
    new_value: any
    timestamp: datetime
    reason: str
    tested_in_paper: bool = False


class OverOptimizationGuard:
    """
    Prevent excessive parameter tuning
    Rules:
    - Same day parameter change ❌
    - Live tuning ❌
    - One bad day = strategy change ❌
    - Weekly review only ✅
    """
    
    def __init__(self, min_review_interval_days: int = 7):
        self.min_review_interval_days = min_review_interval_days
        self.parameter_history: List[ParameterChange] = []
        self.last_review_date: Optional[datetime] = None
        self.current_parameters: Dict = {}
        
        # Flags
        self.parameters_locked = False
        self.lock_reason: Optional[str] = None
    
    def lock_parameters(self, reason: str = "Live trading active"):
        """Lock parameters to prevent changes"""
        self.parameters_locked = True
        self.lock_reason = reason
        self.last_review_date = datetime.now()
    
    def unlock_parameters(self):
        """Unlock for review"""
        self.parameters_locked = False
        self.lock_reason = None
    
    def can_modify_parameters(self) -> Dict:
        """
        Check if parameters can be modified
        
        Rules:
        1. Not locked for live trading
        2. Minimum interval since last review
        3. Must be tested in paper first
        """
        if self.parameters_locked:
            return {
                'allowed': False,
                'reason': f'Parameters locked: {self.lock_reason}'
            }
        
        if self.last_review_date:
            days_since_review = (datetime.now() - self.last_review_date).days
            
            if days_since_review < self.min_review_interval_days:
                return {
                    'allowed': False,
                    'reason': f'Review interval not met: {days_since_review}/{self.min_review_interval_days} days'
                }
        
        return {
            'allowed': True,
            'reason': 'Review interval met, parameters can be modified'
        }
    
    def propose_parameter_change(self, param_name: str, new_value: any, reason: str) -> Dict:
        """
        Propose a parameter change
        Must be approved and tested before live use
        """
        can_modify = self.can_modify_parameters()
        
        if not can_modify['allowed']:
            return {
                'approved': False,
                'reason': can_modify['reason']
            }
        
        old_value = self.current_parameters.get(param_name)
        
        change = ParameterChange(
            parameter_name=param_name,
            old_value=old_value,
            new_value=new_value,
            timestamp=datetime.now(),
            reason=reason,
            tested_in_paper=False
        )
        
        self.parameter_history.append(change)
        
        return {
            'approved': True,
            'reason': 'Change proposed - must test in paper mode first',
            'change_id': len(self.parameter_history) - 1
        }
    
    def mark_tested_in_paper(self, change_id: int, test_results: Dict):
        """
        Mark parameter change as tested in paper mode
        Required before live deployment
        """
        if 0 <= change_id < len(self.parameter_history):
            self.parameter_history[change_id].tested_in_paper = True
            
            # If test passed, apply the change
            if test_results.get('passed', False):
                change = self.parameter_history[change_id]
                self.current_parameters[change.parameter_name] = change.new_value
                return True
        
        return False
    
    def get_recent_changes(self, days: int = 30) -> List[ParameterChange]:
        """Get parameter changes in last N days"""
        cutoff = datetime.now() - timedelta(days=days)
        return [c for c in self.parameter_history if c.timestamp >= cutoff]
    
    def detect_overtuning(self) -> Dict:
        """
        Detect signs of over-optimization
        
        Signs:
        - Too many recent changes
        - Same parameter changed multiple times
        - Changes without paper testing
        """
        recent_changes = self.get_recent_changes(days=14)  # Last 2 weeks
        
        issues = []
        
        # Too many changes
        if len(recent_changes) > 5:
            issues.append(f'Too many recent changes: {len(recent_changes)} in 2 weeks')
        
        # Untested changes
        untested = [c for c in recent_changes if not c.tested_in_paper]
        if untested:
            issues.append(f'{len(untested)} changes not tested in paper mode')
        
        # Same parameter changed multiple times
        param_counts = {}
        for change in recent_changes:
            param_counts[change.parameter_name] = param_counts.get(change.parameter_name, 0) + 1
        
        for param, count in param_counts.items():
            if count > 2:
                issues.append(f'{param} changed {count} times - possible over-fitting')
        
        return {
            'overtuning_detected': len(issues) > 0,
            'issues': issues,
            'recent_changes_count': len(recent_changes)
        }


class LiveReadinessChecklist:
    """
    Pre-trading day checklist
    Ensure everything is ready before going live
    """
    
    def __init__(self):
        self.checklist_items = {
            'config_locked': False,
            'kill_switch_tested': False,
            'max_loss_set': False,
            'logs_clean': False,
            'broker_healthy': False,
            'data_feed_active': False,
            'risk_limits_verified': False,
            'position_sizing_verified': False
        }
        
        self.checklist_results: Dict = {}
        self.last_check_time: Optional[datetime] = None
    
    def check_config_locked(self, guard: OverOptimizationGuard) -> bool:
        """Verify configuration is locked"""
        locked = guard.parameters_locked
        self.checklist_items['config_locked'] = locked
        self.checklist_results['config_locked'] = {
            'passed': locked,
            'message': 'Config locked for trading' if locked else 'Config not locked - UNSAFE'
        }
        return locked
    
    def test_kill_switch(self, kill_switch_callback: callable) -> bool:
        """Test kill switch functionality"""
        try:
            # Dry run test
            result = kill_switch_callback(dry_run=True)
            passed = result is not None
            
            self.checklist_items['kill_switch_tested'] = passed
            self.checklist_results['kill_switch_tested'] = {
                'passed': passed,
                'message': 'Kill switch functional' if passed else 'Kill switch test failed'
            }
            return passed
        except Exception as e:
            self.checklist_results['kill_switch_tested'] = {
                'passed': False,
                'message': f'Kill switch error: {str(e)}'
            }
            return False
    
    def verify_max_loss(self, max_loss_config: float) -> bool:
        """Verify max loss limit is set"""
        passed = max_loss_config > 0
        
        self.checklist_items['max_loss_set'] = passed
        self.checklist_results['max_loss_set'] = {
            'passed': passed,
            'message': f'Max loss set to ₹{max_loss_config:,.0f}' if passed else 'Max loss not configured'
        }
        return passed
    
    def check_logs_clean(self, log_dir: Path) -> bool:
        """Verify logs are ready"""
        try:
            log_dir = Path(log_dir)
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # Check if writable
            test_file = log_dir / '.write_test'
            test_file.touch()
            test_file.unlink()
            
            passed = True
            self.checklist_items['logs_clean'] = passed
            self.checklist_results['logs_clean'] = {
                'passed': passed,
                'message': f'Logs ready at {log_dir}'
            }
            return passed
        except Exception as e:
            self.checklist_results['logs_clean'] = {
                'passed': False,
                'message': f'Log directory error: {str(e)}'
            }
            return False
    
    def test_broker_connection(self, broker_test_func: callable) -> bool:
        """Test broker API connection"""
        try:
            result = broker_test_func()
            passed = result is True
            
            self.checklist_items['broker_healthy'] = passed
            self.checklist_results['broker_healthy'] = {
                'passed': passed,
                'message': 'Broker connection OK' if passed else 'Broker connection failed'
            }
            return passed
        except Exception as e:
            self.checklist_results['broker_healthy'] = {
                'passed': False,
                'message': f'Broker error: {str(e)}'
            }
            return False
    
    def verify_data_feed(self, data_test_func: callable) -> bool:
        """Verify market data feed is active"""
        try:
            result = data_test_func()
            passed = result is True
            
            self.checklist_items['data_feed_active'] = passed
            self.checklist_results['data_feed_active'] = {
                'passed': passed,
                'message': 'Data feed active' if passed else 'Data feed inactive'
            }
            return passed
        except Exception as e:
            self.checklist_results['data_feed_active'] = {
                'passed': False,
                'message': f'Data feed error: {str(e)}'
            }
            return False
    
    def verify_risk_limits(self, risk_config: Dict) -> bool:
        """Verify risk limits are reasonable"""
        required = ['max_drawdown', 'max_trades_per_day', 'risk_per_trade']
        
        passed = all(key in risk_config for key in required)
        
        if passed:
            # Check if values are reasonable
            if risk_config.get('max_drawdown', 0) > 20:
                passed = False
                message = 'Max drawdown too high (>20%)'
            elif risk_config.get('risk_per_trade', 0) > 5:
                passed = False
                message = 'Risk per trade too high (>5%)'
            else:
                message = 'Risk limits verified'
        else:
            message = 'Missing risk configuration'
        
        self.checklist_items['risk_limits_verified'] = passed
        self.checklist_results['risk_limits_verified'] = {
            'passed': passed,
            'message': message
        }
        return passed
    
    def verify_position_sizing(self, sizing_config: Dict) -> bool:
        """Verify position sizing logic"""
        required = ['min_lots', 'max_lots', 'lot_size']
        
        passed = all(key in sizing_config for key in required)
        
        if passed:
            message = f"Position sizing: {sizing_config['min_lots']}-{sizing_config['max_lots']} lots"
        else:
            message = 'Position sizing not configured'
        
        self.checklist_items['position_sizing_verified'] = passed
        self.checklist_results['position_sizing_verified'] = {
            'passed': passed,
            'message': message
        }
        return passed
    
    def run_full_checklist(self, 
                          guard: OverOptimizationGuard,
                          kill_switch_callback: callable,
                          broker_test_func: callable,
                          data_test_func: callable,
                          max_loss_config: float,
                          risk_config: Dict,
                          sizing_config: Dict,
                          log_dir: Path) -> Dict:
        """
        Run complete pre-trading checklist
        
        Returns full report with pass/fail for each item
        """
        self.last_check_time = datetime.now()
        
        # Run all checks
        self.check_config_locked(guard)
        self.test_kill_switch(kill_switch_callback)
        self.verify_max_loss(max_loss_config)
        self.check_logs_clean(log_dir)
        self.test_broker_connection(broker_test_func)
        self.verify_data_feed(data_test_func)
        self.verify_risk_limits(risk_config)
        self.verify_position_sizing(sizing_config)
        
        # Calculate overall status
        all_passed = all(self.checklist_items.values())
        
        failed_items = [k for k, v in self.checklist_items.items() if not v]
        
        return {
            'ready_for_live': all_passed,
            'checklist_time': self.last_check_time.isoformat(),
            'items': self.checklist_items,
            'results': self.checklist_results,
            'failed_items': failed_items,
            'summary': 'ALL SYSTEMS GO ✅' if all_passed else f'FAILED: {", ".join(failed_items)} ❌'
        }
    
    def generate_checklist_report(self) -> str:
        """Generate human-readable checklist report"""
        if not self.checklist_results:
            return "Checklist not run yet"
        
        report = """
╔══════════════════════════════════════════════════════════╗
║         LIVE TRADING READINESS CHECKLIST                 ║
╚══════════════════════════════════════════════════════════╝

"""
        
        for item, result in self.checklist_results.items():
            status = "✅" if result['passed'] else "❌"
            report += f"{status} {item.replace('_', ' ').title()}\n"
            report += f"   {result['message']}\n\n"
        
        all_passed = all(self.checklist_items.values())
        
        if all_passed:
            report += "═══════════════════════════════════════════════════════════\n"
            report += "🚀 ALL SYSTEMS GO - READY FOR LIVE TRADING\n"
            report += "═══════════════════════════════════════════════════════════\n"
        else:
            failed = [k for k, v in self.checklist_items.items() if not v]
            report += "═══════════════════════════════════════════════════════════\n"
            report += "⚠️  NOT READY - RESOLVE ISSUES FIRST\n"
            report += f"Failed items: {', '.join(failed)}\n"
            report += "═══════════════════════════════════════════════════════════\n"
        
        return report
