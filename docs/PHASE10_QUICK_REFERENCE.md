# PHASE 10 — QUICK REFERENCE

**Auto-Learning / Adaptive Logic**

---

## 🚀 30-Second Start

```python
from src.adaptive.adaptive_controller import AdaptiveController

# Initialize
controller = AdaptiveController(config={'adaptive_enabled': True})

# Evaluate signal
decision = controller.evaluate_signal(
    market_data={'vix': 19.5, 'higher_highs': True, ...},
    signal_data={'time': datetime.now(), 'bias_strength': 0.75, ...},
    recent_trades=[...]
)

# Trade or block
if decision.should_trade:
    size = base_size * decision.recommended_size
else:
    print(f"Blocked: {decision.block_reason}")

# Record outcome
controller.record_trade_outcome({
    'won': True,
    'pnl': 450.0,
    'entry_time': ...,
    'exit_time': ...,
    ...
})

# Daily learning (EOD)
summary = controller.run_daily_learning()
```

---

## 📚 Core Components

### 1. Learning Engine
```python
from src.adaptive.learning_engine import LearningEngine

engine = LearningEngine()

# Ingest trade
engine.ingest_trade(trade_features)

# Analyze patterns
insights = engine.analyze_patterns()

# Insights: AMPLIFY / RESTRICT / BLOCK / NEUTRAL
```

### 2. Regime Detector
```python
from src.adaptive.regime_detector import MarketRegimeDetector

detector = MarketRegimeDetector()

# Detect regime
regime = detector.detect_regime(signals)

# Regime types:
# - TRENDING_BULLISH / TRENDING_BEARISH
# - CHOPPY
# - HIGH_VOLATILITY / LOW_VOLATILITY
# - EVENT_DRIVEN
# - NORMAL
```

### 3. Weight Adjuster
```python
from src.adaptive.weight_adjuster import AdaptiveWeightAdjuster

adjuster = AdaptiveWeightAdjuster()

# Apply insights
adjuster.apply_learning_insights(insights)

# Get weight
weight = adjuster.get_weight_for_bucket(RuleType.TIME_FILTER, FeatureBucket.TIME_OPENING)

# Check allowed
allowed = adjuster.should_allow_trade_in_bucket(bucket)
```

### 4. Confidence Scorer
```python
from src.adaptive.confidence_scorer import ConfidenceScorer

scorer = ConfidenceScorer()

# Score signal
confidence = scorer.score_signal(
    signal_buckets=[...],
    bucket_performance={...},
    current_regime=MarketRegime.CHOPPY,
    recent_trades=[...]
)

# Levels: VERY_LOW / LOW / MEDIUM / HIGH / VERY_HIGH
```

### 5. Pattern Detector
```python
from src.adaptive.pattern_detector import LossPatternDetector

detector = LossPatternDetector()

# Analyze history
patterns = detector.analyze_trade_history(trade_history)

# Check if blocked
blocked, reason = detector.is_bucket_blocked(FeatureBucket.TIME_OPENING)
```

### 6. Safety Guard
```python
from src.adaptive.safety_guard import SafetyGuardSystem

guard = SafetyGuardSystem()

# Check learning allowed
check = guard.check_learning_allowed()

# Propose update
proposal = guard.propose_learning_update("WEIGHT_ADJUSTMENT", data, confidence=0.75)

# Auto-review
guard.auto_review_proposals()
```

### 7. Adaptive Controller (Master)
```python
from src.adaptive.adaptive_controller import AdaptiveController

controller = AdaptiveController(config={'adaptive_enabled': True})

# Main workflow
decision = controller.evaluate_signal(market_data, signal_data, recent_trades)
controller.record_trade_outcome(trade_result)
summary = controller.run_daily_learning()
status = controller.get_adaptive_status()
```

---

## 🔑 Key Enums

### FeatureBucket
```python
# Time
TIME_OPENING      # 9:15-9:30 AM
TIME_MORNING      # 9:30-11:00 AM
TIME_LUNCH        # 11:00-1:00 PM
TIME_AFTERNOON    # 1:00-2:30 PM
TIME_CLOSING      # 2:30-3:30 PM

# Bias
BIAS_HIGH         # > 0.7
BIAS_MEDIUM       # 0.4-0.7
BIAS_LOW          # < 0.4

# Greeks
GREEKS_HIGH_GAMMA  # Gamma > 0.05
GREEKS_HIGH_THETA  # |Theta| > 50
GREEKS_NEUTRAL     # Normal

# OI
OI_STRONG         # High conviction
OI_MEDIUM         # Medium conviction
OI_WEAK           # Low conviction

# Volatility
VOL_HIGH          # VIX > 20
VOL_NORMAL        # VIX 12-20
VOL_LOW           # VIX < 12
```

### MarketRegime
```python
TRENDING_BULLISH
TRENDING_BEARISH
CHOPPY
HIGH_VOLATILITY
LOW_VOLATILITY
EVENT_DRIVEN
NORMAL
```

### ConfidenceLevel
```python
VERY_LOW   # < 30%
LOW        # 30-50%
MEDIUM     # 50-70%
HIGH       # 70-85%
VERY_HIGH  # > 85%
```

### PatternSeverity
```python
LOW       # 3-4 losses
MEDIUM    # 4-6 losses
HIGH      # 6-10 losses
CRITICAL  # 10+ losses
```

---

## 📊 Decision Flow

```
Market Data → Regime Detection
             ↓
Signal Data → Bucket Extraction
             ↓
      Pattern Check (blocks?)
             ↓
      Confidence Scoring
             ↓
      Weight Application
             ↓
   Size & Frequency Adjustment
             ↓
      Final Decision (Trade/Block)
             ↓
        Explanation
```

---

## 🛡️ Safety Limits

```python
MIN_LEARNING_INTERVAL = 24 hours
MAX_DAILY_ADJUSTMENTS = 5
MAX_WEIGHT_CHANGE = ±0.5
MIN_SAMPLE_SIZE = 20
MAX_CONSECUTIVE_WINS_CAUTION = 5
```

---

## 📈 Confidence Scoring Formula

```python
score = (
    historical_success * 0.40 +    # Past performance
    regime_match * 0.25 +          # Regime alignment
    recent_performance * 0.20 +    # Recent wins/losses
    sample_size_score * 0.15       # Data adequacy
)
```

**Size Recommendations:**
- VERY_LOW: 0%
- LOW: 50%
- MEDIUM: 80%
- HIGH: 100%
- VERY_HIGH: 120%

---

## 🎯 Learning Insights

### AMPLIFY
```python
LearningInsight(
    bucket=FeatureBucket.TIME_AFTERNOON,
    type='AMPLIFY',
    reason='75.0% win rate in AFTERNOON',
    confidence=0.75,
    recommendation='Prioritize trades during AFTERNOON'
)
```

### RESTRICT
```python
LearningInsight(
    bucket=FeatureBucket.TIME_OPENING,
    type='RESTRICT',
    reason='Only 35.0% win rate in OPENING',
    confidence=0.65,
    recommendation='Reduce trades during OPENING'
)
```

### BLOCK
```python
LearningInsight(
    bucket=FeatureBucket.TIME_OPENING,
    type='BLOCK',
    reason='6 consecutive losses in OPENING',
    confidence=0.85,
    recommendation='Block trades during OPENING'
)
```

---

## 🚨 Loss Patterns

### Detection
```python
LossPattern(
    pattern_type=PatternType.TEMPORAL,
    characteristic='OPENING',
    severity=PatternSeverity.HIGH,
    occurrences=6,
    total_loss=1500.0,
    recommended_action='BLOCK',
    block_duration_hours=72
)
```

### Auto-Blocking
- **HIGH severity**: 72h block
- **CRITICAL severity**: 168h block

---

## 💾 State Management

### Export
```python
state = controller.export_state()
# state = {
#     'weights': {...},
#     'learning_history': {...},
#     'patterns': {...},
#     'last_update': '...'
# }

with open('adaptive_state.json', 'w') as f:
    json.dump(state, f)
```

### Import
```python
with open('adaptive_state.json', 'r') as f:
    state = json.load(f)

controller.import_state(state)
```

---

## 🔧 Common Tasks

### Check if Learning Allowed
```python
check = controller.safety_guard.check_learning_allowed()
if check.passed:
    # Run learning
    summary = controller.run_daily_learning()
else:
    print(f"Not allowed: {check.reason}")
```

### Get Current Regime
```python
status = controller.get_adaptive_status()
regime = status['regime']

print(f"Regime: {regime['regime']}")
print(f"Confidence: {regime['confidence']:.1%}")
print(f"Posture: {regime['description']}")
```

### Check Active Blocks
```python
status = controller.get_adaptive_status()
blocks = status['patterns']['active_blocks']

for block in blocks:
    print(f"🚫 {block['bucket']}: {block['reason']} ({block['remaining_hours']:.1f}h)")
```

### Get Weight Adjustments
```python
status = controller.get_adaptive_status()

# Restrictions
for restriction in status['weights']['active_restrictions']:
    print(f"⚠️ {restriction['bucket']}: {restriction['weight']:.2f}x")

# Amplifications
for amplification in status['weights']['active_amplifications']:
    print(f"✅ {amplification['bucket']}: {amplification['weight']:.2f}x")
```

### Emergency Reset
```python
# Reset all weights to baseline
controller.emergency_reset()

# Disable adaptive
controller.enabled = False
```

---

## 📱 Integration Example

```python
class AngelXBot:
    def __init__(self):
        self.adaptive = AdaptiveController(config={'adaptive_enabled': True})
        # ... other components
    
    def evaluate_signal(self, signal):
        # Get adaptive decision
        decision = self.adaptive.evaluate_signal(
            market_data=self.get_market_data(),
            signal_data=signal,
            recent_trades=self.get_recent_trades()
        )
        
        # Check decision
        if not decision.should_trade:
            self.log(f"🚫 Blocked: {decision.block_reason}")
            return None
        
        # Adjust size
        base_size = self.calculate_base_size()
        adjusted_size = base_size * decision.recommended_size
        
        self.log(f"✅ Trade: {adjusted_size:.0f} lots | "
                 f"Confidence: {decision.confidence.confidence_level.value}")
        
        return {'symbol': signal['symbol'], 'size': adjusted_size}
    
    def on_trade_complete(self, trade):
        # Record outcome
        self.adaptive.record_trade_outcome({
            'entry_time': trade.entry_time,
            'exit_time': trade.exit_time,
            'bias_strength': trade.bias_strength,
            'oi_conviction': trade.oi_conviction,
            'won': trade.pnl > 0,
            'pnl': trade.pnl,
            # ... other features
        })
    
    def end_of_day(self):
        # Run daily learning
        summary = self.adaptive.run_daily_learning()
        
        self.log(f"📚 Daily Learning:")
        self.log(f"  - Insights: {summary['insights_generated']}")
        self.log(f"  - Patterns: {summary['loss_patterns_detected']}")
        self.log(f"  - Proposals: {summary['proposals_approved']}")
        
        # Export state
        self.adaptive.export_state("logs/adaptive_state.json")
```

---

## 🎯 Testing

```bash
# Run demo
python3 scripts/phase10_adaptive_demo.py
```

**Demo shows:**
- ✅ Signal evaluation
- ✅ Learning from 50 trades
- ✅ Loss pattern detection
- ✅ Safety guard enforcement
- ✅ Complete status display

---

## 🧠 Philosophy

**Learning ≠ Prediction**
- Bot শিখে **কখন ট্রেড কমাবে**
- Bot শিখে **কোন condition ignore করবে**
- Bot শিখে **কখন বেশি strict হবে**

**Learning = Filter & Control**
- Rules পাল্টায় না
- Weights পাল্টায়
- Edge amplify করে
- Bad edge restrict করে

**Safety First**
- Daily learning only
- Proposal review cycle
- Emergency reset
- Human override

---

## ✅ Phase 10 Complete!

**Angel-X is now:**
- 🧠 Self-learning
- 🌍 Market-aware
- 🛡️ Safe-guarded
- 📊 Transparent
- ✋ Human-controlled

**Status:** Production Ready 🎯
