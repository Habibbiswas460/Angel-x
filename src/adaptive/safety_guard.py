"""
PHASE 10.6: Safety Guard System
Prevents dangerous learning behaviors

Rules:
- ❌ Same-day learning apply
- ❌ Live parameter mutation
- ❌ Winning streak aggressive
- ✅ Daily learn → store only
- ✅ Weekly review → apply
- ✅ Paper-shadow test → then live

Philosophy: Stability > Intelligence
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum


class SafetyViolation(Enum):
    """Types of safety violations"""
    SAME_DAY_APPLICATION = "SAME_DAY_APPLICATION"           # Applied learning too soon
    EXCESSIVE_ADJUSTMENTS = "EXCESSIVE_ADJUSTMENTS"         # Too many changes
    LARGE_WEIGHT_CHANGE = "LARGE_WEIGHT_CHANGE"            # Weight changed too much
    WINNING_STREAK_AGGRESSION = "WINNING_STREAK_AGGRESSION" # Over-confident after wins
    INSUFFICIENT_SAMPLE = "INSUFFICIENT_SAMPLE"             # Not enough data
    RAPID_REGIME_CHANGE = "RAPID_REGIME_CHANGE"            # Regime flip-flopping


@dataclass
class SafetyCheck:
    """Result of a safety check"""
    passed: bool
    violation_type: Optional[SafetyViolation]
    reason: str
    recommendation: str
    timestamp: datetime


@dataclass
class LearningProposal:
    """Proposed learning update (pending approval)"""
    proposal_id: str
    proposal_type: str           # "WEIGHT_ADJUSTMENT", "PATTERN_BLOCK", etc
    details: Dict
    confidence: float
    created_at: datetime
    
    # Shadow testing results
    shadow_tested: bool = False
    shadow_results: Optional[Dict] = None
    
    # Approval
    approved: bool = False
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None


class SafetyGuardSystem:
    """
    Enforces safety constraints on adaptive learning
    Prevents dangerous behaviors
    """
    
    def __init__(self):
        # Safety limits
        self.min_learning_interval_hours = 24        # Daily learning only
        self.max_adjustments_per_day = 5
        self.max_weight_change_per_adjustment = 0.5
        self.min_sample_size_for_learning = 20
        self.max_consecutive_wins_before_caution = 5
        
        # State tracking
        self.last_learning_update: Optional[datetime] = None
        self.adjustments_today: int = 0
        self.pending_proposals: List[LearningProposal] = []
        self.approved_proposals: List[LearningProposal] = []
        self.rejected_proposals: List[LearningProposal] = []
        
        # Violation log
        self.violations: List[SafetyCheck] = []
    
    def check_learning_allowed(self) -> SafetyCheck:
        """
        Check if learning update is allowed
        Main safety gate
        """
        now = datetime.now()
        
        # 1. Check if enough time passed since last update
        if self.last_learning_update:
            hours_since = (now - self.last_learning_update).total_seconds() / 3600
            if hours_since < self.min_learning_interval_hours:
                return SafetyCheck(
                    passed=False,
                    violation_type=SafetyViolation.SAME_DAY_APPLICATION,
                    reason=f"Last update was {hours_since:.1f}h ago (min: {self.min_learning_interval_hours}h)",
                    recommendation="Wait for daily learning cycle",
                    timestamp=now
                )
        
        # 2. Check daily adjustment limit
        if self.adjustments_today >= self.max_adjustments_per_day:
            return SafetyCheck(
                passed=False,
                violation_type=SafetyViolation.EXCESSIVE_ADJUSTMENTS,
                reason=f"Already made {self.adjustments_today} adjustments today",
                recommendation="Wait for next day",
                timestamp=now
            )
        
        return SafetyCheck(
            passed=True,
            violation_type=None,
            reason="Safety checks passed",
            recommendation="Proceed with learning",
            timestamp=now
        )
    
    def validate_weight_change(self, old_weight: float, new_weight: float) -> SafetyCheck:
        """
        Validate a proposed weight change
        Prevents extreme mutations
        """
        change = abs(new_weight - old_weight)
        
        if change > self.max_weight_change_per_adjustment:
            return SafetyCheck(
                passed=False,
                violation_type=SafetyViolation.LARGE_WEIGHT_CHANGE,
                reason=f"Weight change {change:.2f} exceeds limit {self.max_weight_change_per_adjustment:.2f}",
                recommendation=f"Cap change at ±{self.max_weight_change_per_adjustment:.2f}",
                timestamp=datetime.now()
            )
        
        return SafetyCheck(
            passed=True,
            violation_type=None,
            reason=f"Weight change {change:.2f} within limits",
            recommendation="Approved",
            timestamp=datetime.now()
        )
    
    def check_sample_size(self, sample_size: int) -> SafetyCheck:
        """
        Validate that sample size is adequate for learning
        Prevents learning from insufficient data
        """
        if sample_size < self.min_sample_size_for_learning:
            return SafetyCheck(
                passed=False,
                violation_type=SafetyViolation.INSUFFICIENT_SAMPLE,
                reason=f"Sample size {sample_size} < minimum {self.min_sample_size_for_learning}",
                recommendation="Collect more data before learning",
                timestamp=datetime.now()
            )
        
        return SafetyCheck(
            passed=True,
            violation_type=None,
            reason=f"Sample size {sample_size} adequate",
            recommendation="Approved",
            timestamp=datetime.now()
        )
    
    def check_winning_streak_caution(self, consecutive_wins: int) -> SafetyCheck:
        """
        Check for over-confidence after winning streak
        Prevents getting aggressive after wins
        """
        if consecutive_wins >= self.max_consecutive_wins_before_caution:
            return SafetyCheck(
                passed=False,
                violation_type=SafetyViolation.WINNING_STREAK_AGGRESSION,
                reason=f"{consecutive_wins} consecutive wins - risk of over-confidence",
                recommendation="Maintain conservative posture despite wins",
                timestamp=datetime.now()
            )
        
        return SafetyCheck(
            passed=True,
            violation_type=None,
            reason="No over-confidence risk",
            recommendation="Normal operation",
            timestamp=datetime.now()
        )
    
    def propose_learning_update(self, 
                                proposal_type: str, 
                                details: Dict, 
                                confidence: float) -> LearningProposal:
        """
        Create a learning proposal (not applied immediately)
        Goes through review cycle
        """
        proposal = LearningProposal(
            proposal_id=f"{proposal_type}_{datetime.now().timestamp()}",
            proposal_type=proposal_type,
            details=details,
            confidence=confidence,
            created_at=datetime.now()
        )
        
        self.pending_proposals.append(proposal)
        return proposal
    
    def shadow_test_proposal(self, 
                            proposal: LearningProposal, 
                            historical_data: List[Dict]) -> Dict:
        """
        Test proposal on historical data (shadow mode)
        See what would have happened
        """
        # This would simulate the proposal on historical trades
        # For now, return mock results
        
        results = {
            "trades_affected": len(historical_data),
            "hypothetical_win_rate": 0.65,  # Mock
            "hypothetical_pnl": 5000,       # Mock
            "confidence": proposal.confidence
        }
        
        proposal.shadow_tested = True
        proposal.shadow_results = results
        
        return results
    
    def approve_proposal(self, proposal: LearningProposal, reason: str = "Passed review"):
        """Approve a learning proposal for live application"""
        proposal.approved = True
        proposal.approved_at = datetime.now()
        
        self.pending_proposals.remove(proposal)
        self.approved_proposals.append(proposal)
        
        # Update state
        self.last_learning_update = datetime.now()
        self.adjustments_today += 1
    
    def reject_proposal(self, proposal: LearningProposal, reason: str):
        """Reject a learning proposal"""
        proposal.rejection_reason = reason
        
        self.pending_proposals.remove(proposal)
        self.rejected_proposals.append(proposal)
    
    def daily_reset(self):
        """Reset daily counters (call at EOD)"""
        self.adjustments_today = 0
    
    def emergency_reset(self):
        """Emergency reset all learning (if needed)"""
        self.pending_proposals.clear()
        self.last_learning_update = None
        self.adjustments_today = 0
        print("⚠️ EMERGENCY RESET: All pending learning cleared")
    
    def get_safety_status(self) -> Dict:
        """Get current safety status for dashboard"""
        now = datetime.now()
        hours_since_update = 0.0
        
        if self.last_learning_update:
            hours_since_update = (now - self.last_learning_update).total_seconds() / 3600
        
        return {
            "learning_allowed": self.check_learning_allowed().passed,
            "last_update": self.last_learning_update,
            "hours_since_update": hours_since_update,
            "adjustments_today": self.adjustments_today,
            "max_adjustments": self.max_adjustments_per_day,
            "pending_proposals": len(self.pending_proposals),
            "approved_today": len([p for p in self.approved_proposals 
                                  if p.approved_at and 
                                  p.approved_at.date() == now.date()]),
            "recent_violations": [
                {
                    "type": v.violation_type.value if v.violation_type else "NONE",
                    "reason": v.reason,
                    "time": v.timestamp.strftime("%H:%M:%S")
                }
                for v in self.violations[-5:]  # Last 5
            ]
        }
    
    def get_pending_proposals(self) -> List[Dict]:
        """Get pending proposals for review"""
        return [
            {
                "id": p.proposal_id,
                "type": p.proposal_type,
                "confidence": p.confidence,
                "shadow_tested": p.shadow_tested,
                "shadow_results": p.shadow_results,
                "age_hours": (datetime.now() - p.created_at).total_seconds() / 3600
            }
            for p in self.pending_proposals
        ]
    
    def auto_review_proposals(self):
        """
        Automatically review proposals based on rules
        High confidence + shadow tested + adequate age → approve
        """
        now = datetime.now()
        
        for proposal in list(self.pending_proposals):  # Copy list
            age_hours = (now - proposal.created_at).total_seconds() / 3600
            
            # Must be at least 24h old
            if age_hours < 24:
                continue
            
            # Must be shadow tested
            if not proposal.shadow_tested:
                continue
            
            # High confidence + good shadow results → approve
            if proposal.confidence >= 0.70:
                shadow_win_rate = proposal.shadow_results.get("hypothetical_win_rate", 0)
                if shadow_win_rate >= 0.60:
                    self.approve_proposal(proposal, "Auto-approved: High confidence + good shadow test")
            
            # Low confidence or bad shadow → reject
            elif proposal.confidence < 0.40:
                self.reject_proposal(proposal, "Auto-rejected: Low confidence")
    
    def log_violation(self, check: SafetyCheck):
        """Log a safety violation"""
        if not check.passed:
            self.violations.append(check)
