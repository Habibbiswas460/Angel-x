"""
PHASE 10.5: Loss Pattern Detector
Detects repeating failure patterns to stop capital bleed

Detects:
- Same type loss repeating
- Same time window losses
- Same Greeks condition losses

Actions:
- Temporary rule block
- Cooldown extension
- Risk reduction
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict

from src.adaptive.learning_engine import FeatureBucket, TradeFeatures


class PatternType(Enum):
    """Types of loss patterns"""
    TEMPORAL = "TEMPORAL"                 # Same time repeating
    GREEKS_SETUP = "GREEKS_SETUP"        # Same Greeks condition
    EXIT_REASON = "EXIT_REASON"          # Same exit failing
    MARKET_CONDITION = "MARKET_CONDITION" # Same regime failing
    COMBINATION = "COMBINATION"           # Multi-factor pattern


class PatternSeverity(Enum):
    """How serious is the pattern"""
    LOW = "LOW"              # 2-3 occurrences
    MEDIUM = "MEDIUM"        # 4-5 occurrences
    HIGH = "HIGH"            # 6+ occurrences
    CRITICAL = "CRITICAL"    # Ongoing bleed


@dataclass
class LossPattern:
    """Detected loss pattern"""
    pattern_type: PatternType
    severity: PatternSeverity
    
    # Pattern details
    characteristic: str           # "OPENING window" or "High Gamma" etc
    occurrences: int
    total_loss: float
    avg_loss: float
    
    # Time range
    first_occurrence: datetime
    last_occurrence: datetime
    
    # Recommended action
    recommended_action: str       # "BLOCK", "REDUCE", "MONITOR"
    block_duration_hours: int
    
    # Supporting trades
    trade_ids: List[int]
    
    def is_active_pattern(self) -> bool:
        """Check if pattern is still recent (last 7 days)"""
        return (datetime.now() - self.last_occurrence).days <= 7
    
    def should_block(self) -> bool:
        """Should this pattern trigger a block?"""
        return self.severity in [PatternSeverity.HIGH, PatternSeverity.CRITICAL]


@dataclass
class PatternBlock:
    """Active block from detected pattern"""
    pattern: LossPattern
    blocked_bucket: FeatureBucket
    block_start: datetime
    block_end: datetime
    reason: str
    
    def is_active(self) -> bool:
        """Check if block still active"""
        return datetime.now() < self.block_end
    
    def get_remaining_hours(self) -> float:
        """Hours remaining in block"""
        if not self.is_active():
            return 0.0
        delta = self.block_end - datetime.now()
        return delta.total_seconds() / 3600


class LossPatternDetector:
    """
    Detects dangerous patterns in losses
    Prevents repeating the same mistakes
    """
    
    def __init__(self):
        # Pattern tracking
        self.detected_patterns: List[LossPattern] = []
        self.active_blocks: List[PatternBlock] = []
        
        # Detection thresholds
        self.min_occurrences_for_pattern = 3     # Need 3+ similar losses
        self.lookback_days = 30                   # Analyze last 30 days
        self.pattern_severity_map = {
            (3, 4): PatternSeverity.LOW,
            (4, 6): PatternSeverity.MEDIUM,
            (6, 10): PatternSeverity.HIGH,
            (10, 999): PatternSeverity.CRITICAL
        }
    
    def analyze_trade_history(self, trade_history: List[TradeFeatures]) -> List[LossPattern]:
        """
        Main analysis function
        Detects all types of loss patterns
        """
        # Filter to losses only
        losses = [t for t in trade_history if not t.won]
        
        # Filter to recent
        cutoff = datetime.now() - timedelta(days=self.lookback_days)
        recent_losses = [t for t in losses if t.timestamp >= cutoff]
        
        patterns = []
        
        # 1. Temporal patterns (time-based)
        patterns.extend(self._detect_temporal_patterns(recent_losses))
        
        # 2. Greeks setup patterns
        patterns.extend(self._detect_greeks_patterns(recent_losses))
        
        # 3. Exit reason patterns
        patterns.extend(self._detect_exit_patterns(recent_losses))
        
        # 4. Market condition patterns
        patterns.extend(self._detect_market_condition_patterns(recent_losses))
        
        # Filter significant patterns
        significant_patterns = [p for p in patterns if p.occurrences >= self.min_occurrences_for_pattern]
        
        self.detected_patterns = significant_patterns
        
        # Update active blocks
        self._update_blocks(significant_patterns)
        
        return significant_patterns
    
    def _detect_temporal_patterns(self, losses: List[TradeFeatures]) -> List[LossPattern]:
        """Detect time-based loss patterns"""
        patterns = []
        
        # Group by time bucket
        time_buckets = defaultdict(list)
        for loss in losses:
            time_buckets[loss.time_bucket].append(loss)
        
        for bucket, bucket_losses in time_buckets.items():
            if len(bucket_losses) >= self.min_occurrences_for_pattern:
                total_loss = sum(abs(t.pnl) for t in bucket_losses)
                severity = self._classify_severity(len(bucket_losses))
                
                # Recommend block duration based on severity
                block_hours = {
                    PatternSeverity.LOW: 24,
                    PatternSeverity.MEDIUM: 48,
                    PatternSeverity.HIGH: 72,
                    PatternSeverity.CRITICAL: 168  # 1 week
                }.get(severity, 24)
                
                patterns.append(LossPattern(
                    pattern_type=PatternType.TEMPORAL,
                    severity=severity,
                    characteristic=bucket.value,
                    occurrences=len(bucket_losses),
                    total_loss=total_loss,
                    avg_loss=total_loss / len(bucket_losses),
                    first_occurrence=bucket_losses[0].timestamp,
                    last_occurrence=bucket_losses[-1].timestamp,
                    recommended_action="BLOCK" if severity.value in ["HIGH", "CRITICAL"] else "REDUCE",
                    block_duration_hours=block_hours,
                    trade_ids=list(range(len(bucket_losses)))
                ))
        
        return patterns
    
    def _detect_greeks_patterns(self, losses: List[TradeFeatures]) -> List[LossPattern]:
        """Detect Greeks-based loss patterns"""
        patterns = []
        
        # Group by Greeks bucket
        greeks_buckets = defaultdict(list)
        for loss in losses:
            greeks_buckets[loss.greeks_bucket].append(loss)
        
        for bucket, bucket_losses in greeks_buckets.items():
            if len(bucket_losses) >= self.min_occurrences_for_pattern:
                total_loss = sum(abs(t.pnl) for t in bucket_losses)
                severity = self._classify_severity(len(bucket_losses))
                
                block_hours = 48 if severity.value in ["HIGH", "CRITICAL"] else 24
                
                patterns.append(LossPattern(
                    pattern_type=PatternType.GREEKS_SETUP,
                    severity=severity,
                    characteristic=bucket.value,
                    occurrences=len(bucket_losses),
                    total_loss=total_loss,
                    avg_loss=total_loss / len(bucket_losses),
                    first_occurrence=bucket_losses[0].timestamp,
                    last_occurrence=bucket_losses[-1].timestamp,
                    recommended_action="REDUCE",
                    block_duration_hours=block_hours,
                    trade_ids=list(range(len(bucket_losses)))
                ))
        
        return patterns
    
    def _detect_exit_patterns(self, losses: List[TradeFeatures]) -> List[LossPattern]:
        """Detect exit-based loss patterns"""
        patterns = []
        
        # Group by exit reason
        exit_reasons = defaultdict(list)
        for loss in losses:
            exit_reasons[loss.exit_reason].append(loss)
        
        for reason, reason_losses in exit_reasons.items():
            if len(reason_losses) >= self.min_occurrences_for_pattern:
                total_loss = sum(abs(t.pnl) for t in reason_losses)
                severity = self._classify_severity(len(reason_losses))
                
                patterns.append(LossPattern(
                    pattern_type=PatternType.EXIT_REASON,
                    severity=severity,
                    characteristic=reason,
                    occurrences=len(reason_losses),
                    total_loss=total_loss,
                    avg_loss=total_loss / len(reason_losses),
                    first_occurrence=reason_losses[0].timestamp,
                    last_occurrence=reason_losses[-1].timestamp,
                    recommended_action="MONITOR",  # Usually informational
                    block_duration_hours=0,
                    trade_ids=list(range(len(reason_losses)))
                ))
        
        return patterns
    
    def _detect_market_condition_patterns(self, losses: List[TradeFeatures]) -> List[LossPattern]:
        """Detect market condition loss patterns"""
        patterns = []
        
        # Group by volatility bucket
        vol_buckets = defaultdict(list)
        for loss in losses:
            vol_buckets[loss.vol_bucket].append(loss)
        
        for bucket, bucket_losses in vol_buckets.items():
            if len(bucket_losses) >= self.min_occurrences_for_pattern:
                total_loss = sum(abs(t.pnl) for t in bucket_losses)
                severity = self._classify_severity(len(bucket_losses))
                
                block_hours = 24 if severity.value in ["HIGH", "CRITICAL"] else 0
                
                patterns.append(LossPattern(
                    pattern_type=PatternType.MARKET_CONDITION,
                    severity=severity,
                    characteristic=bucket.value,
                    occurrences=len(bucket_losses),
                    total_loss=total_loss,
                    avg_loss=total_loss / len(bucket_losses),
                    first_occurrence=bucket_losses[0].timestamp,
                    last_occurrence=bucket_losses[-1].timestamp,
                    recommended_action="REDUCE" if severity.value in ["HIGH", "CRITICAL"] else "MONITOR",
                    block_duration_hours=block_hours,
                    trade_ids=list(range(len(bucket_losses)))
                ))
        
        return patterns
    
    def _classify_severity(self, occurrences: int) -> PatternSeverity:
        """Classify pattern severity"""
        for (min_occ, max_occ), severity in self.pattern_severity_map.items():
            if min_occ <= occurrences < max_occ:
                return severity
        return PatternSeverity.CRITICAL
    
    def _update_blocks(self, patterns: List[LossPattern]):
        """Update active blocks based on detected patterns"""
        # Remove expired blocks
        self.active_blocks = [b for b in self.active_blocks if b.is_active()]
        
        # Add new blocks for HIGH/CRITICAL patterns
        for pattern in patterns:
            if pattern.should_block():
                # Check if already blocked
                already_blocked = any(
                    b.pattern.characteristic == pattern.characteristic
                    for b in self.active_blocks
                )
                
                if not already_blocked:
                    # Map characteristic to bucket
                    bucket = self._get_bucket_from_characteristic(pattern)
                    if bucket:
                        block = PatternBlock(
                            pattern=pattern,
                            blocked_bucket=bucket,
                            block_start=datetime.now(),
                            block_end=datetime.now() + timedelta(hours=pattern.block_duration_hours),
                            reason=f"{pattern.pattern_type.value}: {pattern.occurrences} losses ({pattern.total_loss:.0f})"
                        )
                        self.active_blocks.append(block)
    
    def _get_bucket_from_characteristic(self, pattern: LossPattern) -> Optional[FeatureBucket]:
        """Convert pattern characteristic to feature bucket"""
        char = pattern.characteristic
        
        # Try to find matching bucket
        for bucket in FeatureBucket:
            if bucket.value == char:
                return bucket
        
        return None
    
    def is_bucket_blocked(self, bucket: FeatureBucket) -> Tuple[bool, Optional[str]]:
        """
        Check if a bucket is currently blocked
        Returns: (is_blocked, reason)
        """
        for block in self.active_blocks:
            if block.blocked_bucket == bucket and block.is_active():
                remaining = block.get_remaining_hours()
                return True, f"{block.reason} (blocked for {remaining:.1f}h more)"
        
        return False, None
    
    def get_pattern_summary(self) -> Dict:
        """Get summary for dashboard"""
        return {
            "total_patterns_detected": len(self.detected_patterns),
            "active_blocks": [
                {
                    "bucket": block.blocked_bucket.value,
                    "reason": block.reason,
                    "remaining_hours": block.get_remaining_hours(),
                    "severity": block.pattern.severity.value
                }
                for block in self.active_blocks if block.is_active()
            ],
            "recent_patterns": [
                {
                    "type": p.pattern_type.value,
                    "characteristic": p.characteristic,
                    "occurrences": p.occurrences,
                    "total_loss": p.total_loss,
                    "severity": p.severity.value,
                    "action": p.recommended_action
                }
                for p in self.detected_patterns[-5:]  # Last 5
            ]
        }
    
    def get_worst_patterns(self, top_n: int = 3) -> List[LossPattern]:
        """Get worst loss patterns"""
        return sorted(self.detected_patterns, 
                     key=lambda p: p.total_loss, 
                     reverse=True)[:top_n]
