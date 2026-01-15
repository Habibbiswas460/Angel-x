"""
Tests for Adaptive Learning Modules
Covers regime detection, pattern detection, and adaptive controller
"""

import pytest
from datetime import datetime, timedelta
from src.adaptive.regime_detector import (
    MarketRegime,
    RegimeSignals,
    RegimeClassification,
    MarketRegimeDetector,
)
from src.adaptive.pattern_detector import (
    PatternType,
    PatternSeverity,
    LossPattern,
    PatternBlock,
    LossPatternDetector,
)


class TestRegimeDetector:
    """Test market regime detection"""

    def test_regime_signals_creation(self):
        """Test creating regime signals"""
        signals = RegimeSignals(
            price_range_pct=2.5,
            higher_highs=True,
            lower_lows=False,
            vix=18.5,
            atr_pct=1.5,
            rate_of_change_5min=0.3,
            rate_of_change_15min=0.8,
            oi_imbalance=0.2,
            iv_expansion=False,
            volume_surge=True,
            timestamp=datetime.now(),
        )

        assert signals.price_range_pct == 2.5
        assert signals.higher_highs is True
        assert signals.vix == 18.5
        assert isinstance(signals.timestamp, datetime)

    def test_regime_classification_bullish(self):
        """Test bullish regime classification"""
        signals = RegimeSignals(
            price_range_pct=1.8,
            higher_highs=True,
            lower_lows=False,
            vix=15.0,
            atr_pct=1.2,
            rate_of_change_5min=0.5,
            rate_of_change_15min=1.2,
            oi_imbalance=0.3,
            iv_expansion=False,
            volume_surge=True,
            timestamp=datetime.now(),
        )

        classification = RegimeClassification(
            regime=MarketRegime.TRENDING_BULLISH,
            confidence=0.85,
            sub_characteristics=["strong_momentum", "high_volume"],
            recommended_trade_frequency="NORMAL",
            recommended_position_size="NORMAL",
            recommended_holding_style="RUNNER",
            signals=signals,
            timestamp=datetime.now(),
        )

        assert classification.regime == MarketRegime.TRENDING_BULLISH
        assert classification.confidence == 0.85
        assert "RUNNER" in classification.get_posture_description()

    def test_regime_classification_choppy(self):
        """Test choppy regime requires reduced trading"""
        signals = RegimeSignals(
            price_range_pct=0.8,
            higher_highs=False,
            lower_lows=False,
            vix=12.0,
            atr_pct=0.5,
            rate_of_change_5min=0.1,
            rate_of_change_15min=-0.1,
            oi_imbalance=0.0,
            iv_expansion=False,
            volume_surge=False,
            timestamp=datetime.now(),
        )

        classification = RegimeClassification(
            regime=MarketRegime.CHOPPY,
            confidence=0.75,
            sub_characteristics=["range_bound", "low_momentum"],
            recommended_trade_frequency="REDUCED",
            recommended_position_size="REDUCED",
            recommended_holding_style="QUICK",
            signals=signals,
            timestamp=datetime.now(),
        )

        assert classification.regime == MarketRegime.CHOPPY
        assert classification.recommended_trade_frequency == "REDUCED"
        assert classification.recommended_position_size == "REDUCED"

    def test_regime_detector_initialization(self):
        """Test regime detector initializes correctly"""
        detector = MarketRegimeDetector()
        assert detector is not None
        assert hasattr(detector, "detect_regime")


class TestPatternDetector:
    """Test loss pattern detection"""

    def test_loss_pattern_creation(self):
        """Test creating a loss pattern"""
        pattern = LossPattern(
            pattern_type=PatternType.TEMPORAL,
            severity=PatternSeverity.MEDIUM,
            characteristic="OPENING_WINDOW",
            occurrences=4,
            total_loss=-8000,
            avg_loss=-2000,
            first_occurrence=datetime.now() - timedelta(days=10),
            last_occurrence=datetime.now() - timedelta(days=2),
            recommended_action="REDUCE",
            block_duration_hours=24,
            trade_ids=[101, 102, 103, 104],
        )

        assert pattern.pattern_type == PatternType.TEMPORAL
        assert pattern.occurrences == 4
        assert pattern.avg_loss == -2000
        assert len(pattern.trade_ids) == 4

    def test_loss_pattern_is_active(self):
        """Test pattern activity check"""
        # Recent pattern - should be active
        recent_pattern = LossPattern(
            pattern_type=PatternType.GREEKS_SETUP,
            severity=PatternSeverity.HIGH,
            characteristic="HIGH_GAMMA",
            occurrences=6,
            total_loss=-12000,
            avg_loss=-2000,
            first_occurrence=datetime.now() - timedelta(days=5),
            last_occurrence=datetime.now() - timedelta(days=1),
            recommended_action="BLOCK",
            block_duration_hours=48,
            trade_ids=[201, 202, 203, 204, 205, 206],
        )

        assert recent_pattern.is_active_pattern() is True

        # Old pattern - should be inactive
        old_pattern = LossPattern(
            pattern_type=PatternType.TEMPORAL,
            severity=PatternSeverity.LOW,
            characteristic="CLOSING_WINDOW",
            occurrences=2,
            total_loss=-3000,
            avg_loss=-1500,
            first_occurrence=datetime.now() - timedelta(days=30),
            last_occurrence=datetime.now() - timedelta(days=10),
            recommended_action="MONITOR",
            block_duration_hours=0,
            trade_ids=[301, 302],
        )

        assert old_pattern.is_active_pattern() is False

    def test_loss_pattern_should_block(self):
        """Test block recommendation logic"""
        # High severity - should block
        high_severity = LossPattern(
            pattern_type=PatternType.EXIT_REASON,
            severity=PatternSeverity.HIGH,
            characteristic="STOP_LOSS_HIT",
            occurrences=7,
            total_loss=-14000,
            avg_loss=-2000,
            first_occurrence=datetime.now() - timedelta(days=5),
            last_occurrence=datetime.now() - timedelta(hours=6),
            recommended_action="BLOCK",
            block_duration_hours=72,
            trade_ids=[401, 402, 403, 404, 405, 406, 407],
        )

        assert high_severity.should_block() is True

        # Low severity - should not block
        low_severity = LossPattern(
            pattern_type=PatternType.MARKET_CONDITION,
            severity=PatternSeverity.LOW,
            characteristic="HIGH_VIX",
            occurrences=2,
            total_loss=-3000,
            avg_loss=-1500,
            first_occurrence=datetime.now() - timedelta(days=3),
            last_occurrence=datetime.now() - timedelta(days=1),
            recommended_action="MONITOR",
            block_duration_hours=0,
            trade_ids=[501, 502],
        )

        assert low_severity.should_block() is False

    def test_pattern_block_creation(self):
        """Test creating a pattern block"""
        from src.adaptive.learning_engine import FeatureBucket

        pattern = LossPattern(
            pattern_type=PatternType.TEMPORAL,
            severity=PatternSeverity.CRITICAL,
            characteristic="OPENING_WINDOW",
            occurrences=10,
            total_loss=-25000,
            avg_loss=-2500,
            first_occurrence=datetime.now() - timedelta(days=14),
            last_occurrence=datetime.now() - timedelta(hours=2),
            recommended_action="BLOCK",
            block_duration_hours=96,
            trade_ids=list(range(601, 611)),
        )

        block_start = datetime.now()
        block_end = block_start + timedelta(hours=96)

        block = PatternBlock(
            pattern=pattern,
            blocked_bucket=FeatureBucket.TIME_OPENING,
            block_start=block_start,
            block_end=block_end,
            reason="CRITICAL: 10 losses in OPENING window",
        )

        assert block.is_active() is True
        assert block.pattern.severity == PatternSeverity.CRITICAL
        # Check approximate duration (within 1 second tolerance)
        duration_hours = (block.block_end - block.block_start).total_seconds() / 3600
        assert 95.99 < duration_hours < 96.01

    def test_pattern_detector_initialization(self):
        """Test pattern detector initializes"""
        detector = LossPatternDetector()
        assert detector is not None
        assert hasattr(detector, "analyze_trade_history")
        assert hasattr(detector, "detected_patterns")
        assert hasattr(detector, "active_blocks")


class TestRegimeEnumValues:
    """Test regime enumeration values"""

    def test_market_regime_enum(self):
        """Test all market regime types exist"""
        assert MarketRegime.TRENDING_BULLISH.value == "TRENDING_BULLISH"
        assert MarketRegime.TRENDING_BEARISH.value == "TRENDING_BEARISH"
        assert MarketRegime.CHOPPY.value == "CHOPPY"
        assert MarketRegime.HIGH_VOLATILITY.value == "HIGH_VOLATILITY"
        assert MarketRegime.LOW_VOLATILITY.value == "LOW_VOLATILITY"
        assert MarketRegime.EVENT_DRIVEN.value == "EVENT_DRIVEN"
        assert MarketRegime.NORMAL.value == "NORMAL"

    def test_pattern_type_enum(self):
        """Test all pattern types exist"""
        assert PatternType.TEMPORAL.value == "TEMPORAL"
        assert PatternType.GREEKS_SETUP.value == "GREEKS_SETUP"
        assert PatternType.EXIT_REASON.value == "EXIT_REASON"
        assert PatternType.MARKET_CONDITION.value == "MARKET_CONDITION"
        assert PatternType.COMBINATION.value == "COMBINATION"

    def test_pattern_severity_enum(self):
        """Test all severity levels exist"""
        assert PatternSeverity.LOW.value == "LOW"
        assert PatternSeverity.MEDIUM.value == "MEDIUM"
        assert PatternSeverity.HIGH.value == "HIGH"
        assert PatternSeverity.CRITICAL.value == "CRITICAL"


class TestRegimeRecommendations:
    """Test regime-based recommendations"""

    def test_high_volatility_regime(self):
        """High volatility should reduce size"""
        signals = RegimeSignals(
            price_range_pct=4.5,
            higher_highs=True,
            lower_lows=True,
            vix=35.0,
            atr_pct=3.5,
            rate_of_change_5min=1.5,
            rate_of_change_15min=-1.2,
            oi_imbalance=0.5,
            iv_expansion=True,
            volume_surge=True,
            timestamp=datetime.now(),
        )

        classification = RegimeClassification(
            regime=MarketRegime.HIGH_VOLATILITY,
            confidence=0.92,
            sub_characteristics=["explosive_moves", "high_vix"],
            recommended_trade_frequency="REDUCED",
            recommended_position_size="MINIMAL",
            recommended_holding_style="QUICK",
            signals=signals,
            timestamp=datetime.now(),
        )

        assert classification.regime == MarketRegime.HIGH_VOLATILITY
        assert classification.recommended_position_size == "MINIMAL"
        assert classification.confidence > 0.9

    def test_event_driven_regime(self):
        """Event-driven markets need caution"""
        signals = RegimeSignals(
            price_range_pct=3.2,
            higher_highs=False,
            lower_lows=False,
            vix=28.0,
            atr_pct=2.8,
            rate_of_change_5min=2.0,
            rate_of_change_15min=1.5,
            oi_imbalance=0.7,
            iv_expansion=True,
            volume_surge=True,
            timestamp=datetime.now(),
        )

        classification = RegimeClassification(
            regime=MarketRegime.EVENT_DRIVEN,
            confidence=0.88,
            sub_characteristics=["news_impact", "iv_spike"],
            recommended_trade_frequency="MINIMAL",
            recommended_position_size="MINIMAL",
            recommended_holding_style="QUICK",
            signals=signals,
            timestamp=datetime.now(),
        )

        assert classification.regime == MarketRegime.EVENT_DRIVEN
        assert classification.recommended_trade_frequency == "MINIMAL"
        assert "EVENT_DRIVEN" in classification.get_posture_description()
