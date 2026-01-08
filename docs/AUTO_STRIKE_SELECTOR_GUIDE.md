# Automatic Strike Selection - User Guide

## Overview
The Automatic Strike Selector intelligently chooses the best option strike from ATM ±3 range based on Greeks quality and IV analysis. It eliminates guesswork and provides data-driven strike selection for optimal entries.

---

## How It Works

### 1. Strike Range Generation
- Centers on ATM (At-The-Money) strike
- Scans ±3 strikes in both directions
- Total 7 strikes analyzed: ATM-3, ATM-2, ATM-1, ATM, ATM+1, ATM+2, ATM+3

**Example:**
- Spot: ₹26,178.70
- Strike interval: 50 (NIFTY)
- ATM: 26200
- Range: 26050, 26100, 26150, **26200**, 26250, 26300, 26350

---

### 2. Greeks Calculation
For each strike, calculates Black-Scholes Greeks:

**Delta** (Directional sensitivity)
- Calls: 0 → 1 (ITM calls have higher delta)
- Puts: 0 → -1 (ITM puts have higher absolute delta)
- Ideal range: 0.40 - 0.65 (balanced)

**Gamma** (Rate of delta change)
- Peaks near ATM
- Higher gamma = more sensitivity to spot moves
- Ideal: > 0.001 for scalping

**Theta** (Time decay)
- Negative for long options
- ATM options decay faster
- Ideal: < -20 per day (controlled decay)

**Vega** (IV sensitivity)
- Higher near ATM
- Measures option price sensitivity to IV changes
- Ideal: 5-15 (moderate exposure)

---

### 3. IV (Implied Volatility) Estimation
IV varies by moneyness:

**OTM Options** (Out-The-Money)
- Higher IV (16-18%)
- More expensive relative to intrinsic value
- Call OTM: strike > spot
- Put OTM: strike < spot

**ATM Options** (At-The-Money)
- Base IV (~16%)
- Balanced pricing
- Strike ≈ spot

**ITM Options** (In-The-Money)
- Lower IV (15-16%)
- Intrinsic value dominates
- Call ITM: strike < spot
- Put ITM: strike > spot

---

### 4. Strike Scoring System

**Greeks Quality (50%)**
- Delta score: 30 points
- Gamma score: 30 points
- Theta score: 20 points
- Vega score: 20 points
- Total: 100 points → 50% weight

**Liquidity (30%)**
- Volume score: 15 points
- OI score: 15 points
- (Currently placeholder, will use real data)

**ATM Proximity Bonus (20%)**
- ATM: +20 points
- ATM±1: +15 points
- ATM±2: +10 points
- ATM±3: +5 points

**Total Score: 0-100**

---

## Usage Examples

### Basic Usage (Python API)

```python
from src.engines.strike_selection.auto_selector import AutoStrikeSelector

# Initialize selector
selector = AutoStrikeSelector(atm_range=3)

# Select optimal strike
selected = selector.select_optimal_strike(
    spot_price=26178.70,
    bias="BULLISH",  # or "BEARISH"
    strike_interval=50,  # 50 for NIFTY, 100 for BANKNIFTY
    days_to_expiry=2.0,
    min_delta=0.35,
    max_delta=0.75,
    prefer_atm=True
)

if selected:
    print(f"Strike: {selected.strike} {selected.option_type}")
    print(f"Delta: {selected.delta:.3f}")
    print(f"Gamma: {selected.gamma:.5f}")
    print(f"Score: {selected.total_score:.1f}")
```

### Command-Line Tool

**NIFTY Bullish Selection:**
```bash
PYTHONPATH=. .venv/bin/python scripts/live_strike_selector.py NIFTY BULLISH
```

**BANKNIFTY Bearish Selection:**
```bash
PYTHONPATH=. .venv/bin/python scripts/live_strike_selector.py BANKNIFTY BEARISH
```

---

## Output Interpretation

### Sample Output
```
✓ RECOMMENDED STRIKE: 26200 CE
  Moneyness: ATM
  LTP Estimate: ₹10.00

  Greeks:
    Delta:  0.472  (Balanced)
    Gamma:  0.00181  (High sensitivity)
    Theta:  -45.92   (Decay/day)
    Vega:   5.45   (IV sensitivity)
    IV:     16.0%

  Scores:
    Greeks:    80.0/100
    Total:     75.0/100
```

### What Each Metric Means

**Delta: 0.472 (Balanced)**
- Option will move ₹0.47 for every ₹1 move in spot
- Not too aggressive (not deep ITM)
- Not too weak (not far OTM)

**Gamma: 0.00181 (High sensitivity)**
- Delta will change by 0.00181 for every ₹1 spot move
- High gamma near ATM = fast delta acceleration
- Good for scalping quick moves

**Theta: -45.92 (Decay/day)**
- Option loses ₹45.92 per day due to time decay
- Need spot to move in your favor to overcome this
- Acceptable for 1-2 day holds

**Vega: 5.45 (IV sensitivity)**
- Option gains ₹5.45 for every 1% increase in IV
- Low vega = less sensitive to volatility changes
- Good for stable IV environments

**IV: 16.0%**
- Current implied volatility estimate
- Reflects market's expectation of future volatility
- Lower than OTM options (less time value)

---

## Strike Ladder Interpretation

```
| Rank   | Strike   | Type | Moneyness | Delta | Gamma   | Score |
|--------|----------|------|-----------|-------|---------|-------|
| ⭐ BEST | 26200 CE | ATM  | ATM       | 0.472 | 0.00181 | 75.0  |
| #2     | 26150 CE | ITM  | ATM-1     | 0.562 | 0.00180 | 70.0  |
| #3     | 26250 CE | OTM  | ATM+1     | 0.383 | 0.00173 | 65.0  |
```

**Best Strike (ATM):**
- Highest score (75.0)
- Balanced delta and gamma
- Peak gamma near ATM

**ITM Alternative (ATM-1):**
- Higher delta (0.562) = more directional
- Similar gamma
- Lower score due to higher cost and lower gamma rank

**OTM Alternative (ATM+1):**
- Lower delta (0.383) = less directional
- Slightly lower gamma
- Cheaper but needs bigger spot move

---

## Decision Guidelines

### When to Prefer ATM
- Balanced risk/reward
- Maximum gamma exposure
- Moderate premium cost
- **Default choice for most entries**

### When to Prefer ITM (ATM-1, ATM-2)
- Strong directional conviction
- Higher delta wanted
- More intrinsic value (less time decay risk)
- **Use when bias is very strong**

### When to Prefer OTM (ATM+1, ATM+2)
- Lower capital requirement
- Willing to accept lower probability
- Need bigger move to profit
- **Use for speculative plays only**

---

## Integration with Strategy

The auto selector integrates seamlessly with Angel-x strategy:

1. **Bias Engine** determines direction (BULLISH/BEARISH)
2. **Entry Engine** confirms entry timing
3. **Auto Strike Selector** chooses optimal strike from ATM ±3
4. **Greeks validation** ensures quality (delta, gamma thresholds)
5. **Position Sizing** calculates quantity
6. **Risk Manager** sets stop loss based on delta/theta
7. **Order Manager** places trade

---

## Advanced Parameters

### Adjustable Thresholds

**Delta Range:**
```python
min_delta=0.35  # Reject weak deltas
max_delta=0.75  # Reject deep ITM
```

**Gamma Minimum:**
```python
min_gamma=0.0005  # Minimum sensitivity required
```

**ATM Preference:**
```python
prefer_atm=True   # Favor strikes near ATM
prefer_atm=False  # Treat all strikes equally
```

**Strike Range:**
```python
AutoStrikeSelector(atm_range=3)  # ATM ±3 (default)
AutoStrikeSelector(atm_range=5)  # ATM ±5 (wider scan)
```

---

## Real-World Scenarios

### Scenario 1: Morning Breakout (NIFTY Bullish)
- Spot: 26178 → Strong uptrend
- Bias: BULLISH
- Auto selector picks: **26200 CE** (ATM)
  - Delta 0.472: Captures 47% of upside
  - Gamma 0.00181: Accelerates as spot rises
  - Theta -45.92: Manageable decay for 1-2 day hold
  - **Result:** Balanced risk/reward for trending day

### Scenario 2: Range-Bound Day (NIFTY Neutral)
- Spot: 26178 → Choppy, no clear direction
- Bias: NEUTRAL
- Auto selector: **No trade recommended**
- **Result:** Capital preserved, no forced entries

### Scenario 3: Strong Conviction (BANKNIFTY Bearish)
- Spot: 56000 → Sharp downtrend
- Bias: BEARISH (very strong)
- Auto selector picks: **55900 PE** (ATM-1, ITM)
  - Delta -0.62: High directional exposure
  - Gamma 0.0008: Good sensitivity
  - Lower IV: Less time value erosion
  - **Result:** Aggressive positioning for high-probability move

---

## Common Questions

**Q: Why not always pick highest delta?**
A: High delta (deep ITM) options have:
- Lower gamma (less acceleration)
- Higher premium (more capital required)
- Lower percentage returns

**Q: Why score ATM so highly?**
A: ATM options offer:
- Maximum gamma (highest sensitivity)
- Balanced delta
- Reasonable premium
- Best risk/reward for scalping

**Q: How does IV affect selection?**
A: IV estimation helps identify:
- OTM options (higher IV = more expensive time value)
- ITM options (lower IV = more intrinsic value)
- Fair pricing assessment

**Q: Can I override the selection?**
A: Yes, the full ladder is displayed. You can:
- Review all 7 strikes
- Choose alternative based on your preference
- Use score as guidance, not absolute rule

---

## Performance Tips

1. **Trust the Score:** Top-ranked strike is usually optimal
2. **Check Moneyness:** Understand ITM/ATM/OTM positioning
3. **Validate Greeks:** Ensure delta/gamma meet your expectations
4. **Consider Theta:** Higher theta = faster decay
5. **Monitor IV:** High IV = expensive, low IV = cheaper

---

## Limitations & Future Enhancements

**Current Limitations:**
- IV is estimated, not live broker IV
- Liquidity score is placeholder (not real volume/OI)
- Greeks calculated via Black-Scholes (model-based)

**Planned Enhancements:**
- Real-time IV from broker Greeks API
- Live volume/OI integration for liquidity scoring
- Historical performance tracking per strike
- Machine learning for IV prediction
- Multi-leg strategy support (spreads, strangles)

---

## Summary

The Automatic Strike Selector removes guesswork by:
- ✓ Scanning ATM ±3 strikes systematically
- ✓ Computing Greeks for each strike
- ✓ Scoring based on quality, not emotion
- ✓ Recommending optimal balance of risk/reward
- ✓ Providing full transparency (all strikes displayed)

**Result:** Data-driven strike selection aligned with Greeks, IV, and strategy goals.

---

For live usage: `scripts/live_strike_selector.py`  
For integration: `src/engines/strike_selection/auto_selector.py`  
For details: See [main.md](../main.md) Behavior Example D
