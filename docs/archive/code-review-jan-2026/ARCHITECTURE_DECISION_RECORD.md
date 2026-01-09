# Architecture Decision Record: Package Structure (app/ vs src/)

**Status**: APPROVED - ACTION REQUIRED  
**Date**: January 9, 2026  
**Severity**: CRITICAL (Production Safety)

## Problem Statement

The codebase contains **two parallel package hierarchies** that create ambiguity and runtime risk:

```
app/
  ├── domains/
  │   ├── trading/
  │   │   ├── order_manager.py ✓ (uses AngelOne adapter)
  │   │   ├── trade_manager.py
  │   │   ├── risk_manager.py
  │   └── options/
  │       └── chain_analyzer.py
  ├── services/
  │   └── broker/
  │       ├── angelone_adapter.py ✓
  │       └── angelone_client.py ✓
  └── utils/
      ├── logger.py
      ├── exceptions.py
      └── ... (no options_helper)

src/
  ├── core/
  │   ├── order_manager.py (OpenAlgo-based)
  │   ├── trade_manager.py
  │   ├── risk_manager.py
  │   └── failover_system.py
  ├── integrations/
  │   ├── angelone/
  │   │   ├── smartapi_integration.py
  │   │   ├── angelone_client.py
  │   │   └── angelone_adapter.py
  │   └── data_feeds/
  │       └── data_feed.py
  ├── engines/
  │   └── greeks/
  │       └── greeks_data_manager.py (uses OpenAlgo)
  └── utils/
      └── options_helper.py ⚠️ (OpenAlgo-based, missing null check)
```

### Risks from Duplication

| Issue | Impact | Example |
|-------|--------|---------|
| **Import ambiguity** | Runtime crashes if wrong import used | `from app.core import OrderManager` vs `from src.core import OrderManager` |
| **Data inconsistency** | Different logic in prod vs test | `app/domains/options/chain_analyzer.py` calls `options_helper.get_option_greeks()` but unclear if it's using app or src version |
| **Dockerfile mismatch** | Container doesn't have copied files | Dockerfile copies `app/`, `infra/`, `tools/`, `scripts/` but NOT `src/` → src imports fail in container |
| **Greeks calculation split** | Unclear data source | `src/engines/greeks/greeks_data_manager.py` uses OpenAlgo; `app/services/broker/angelone_adapter.py` claims AngelOne but may fallback to src |
| **Test integrity** | Test mode wiring broken | Test harness imports unclear—may execute real trades via wrong path |

## Decision: Canonical Package Strategy

**Adopt `app/` as the canonical production package. Deprecate `src/`.**

### Rationale

1. **app/** already has correct anti-patterns:
   - Proper broker integration (AngelOneAdapter ✓)
   - Structured domain model (app/domains/trading, app/domains/options)
   - Real production code flow main.py → app.engines/app.domains

2. **src/** was experimental:
   - Contains OpenAlgo-hardcoded code (options_helper, greeks_data_manager)
   - Duplication of OrderManager, TradeManager, RiskManager (unclear intent)
   - Not properly integrated into Dockerfile

3. **main.py already imports from app/**:
   ```python
   from app.integrations.angelone.angelone_adapter import AngelOneAdapter
   from app.domains.trading.order_manager import OrderManager
   from app.engines.greeks.greeks_data_manager import GreeksDataManager
   ```

### Migration Plan

#### Phase 1: Immediate (This PR)
- [ ] **Remove src/ from Dockerfile COPY** → prevents accidental imports
- [ ] **Update all imports in app/** to be internal (app.* only)
- [ ] **Verify main.py imports** work with app/ only
- [ ] **Move app/engines/greeks/greeks_data_manager.py to app/engines/** (if exists)

#### Phase 2: Code Consolidation (Next Sprint)
- [ ] **Audit which code is actually used** in prod (TradeManager from app or src?)
- [ ] **Merge app/domains/trading/{order_manager, trade_manager, risk_manager}** with duplicates
- [ ] **Move app/services/broker/angelone_*** to app/integrations/angelone/**
- [ ] **Remove src/ directory entirely** or mark as deprecated

#### Phase 3: Testing & Validation (Before Release)
- [ ] **Unit tests** import only from app.* (run in CI)
- [ ] **Integration tests** with docker-compose verify healthcheck works
- [ ] **Live paper trading test** (Phase Test0 → Test8) uses app/ paths only

## Implementation Checklist

### 1. Dockerfile Fix (✓ DONE)
```dockerfile
# OLD: Copies app/, infra/, tools/, scripts/ but not src/
# NEW: Copy only app/, infra/, tools/, scripts/
# src/ will no longer be available in container
COPY app infra tools scripts config main.py requirements.txt /app/
```

### 2. Config Consistency (✓ DONE)
- [x] Removed hardcoded `DATABASE_PASSWORD = "angelx_secure_2026"` in infra/config/*.py
- [x] Added production safety gate: missing DB_PASSWORD raises ValueError in production

### 3. Greeks/Options Data Source Clarity (IN PROGRESS)
**Current state:**
- `src/utils/options_helper.py` → OpenAlgo client
- `src/engines/greeks/greeks_data_manager.py` → calls options_helper.get_option_greeks()
- `app/domains/options/chain_analyzer.py` → also calls options_helper.get_option_greeks() (unclear which one)
- `app/services/broker/angelone_adapter.py` → claims AngelOne SmartAPI

**Action required:**
Confirm which is used in live trading:
```bash
grep -r "get_option_greeks\|GreeksDataManager" app/ --include="*.py"
grep -r "from.*greeks" main.py app/
```

If **AngelOne SmartAPI** is the intent:
- Move OpenAlgo-based code to `src/legacy/` (quarantine)
- Implement Greeks in AngelOne adapter directly
- Update config DATA_SOURCE strategy

If **OpenAlgo** is required:
- Move `src/utils/options_helper.py` → `app/utils/options_helper.py`
- Remove duplicates from src/
- Keep src/ for alternative implementations only (marked as legacy)

### 4. Trading Safety Enforcement (PENDING)
**Ensure single point of truth for TRADING_ENABLED:**

```python
# app/domains/trading/order_manager.py (SINGLE SOURCE)
class OrderManager:
    def place_order(self, ...):
        if not getattr(config, 'TRADING_ENABLED', False):
            logger.warning("TRADING_ENABLED=False; order blocked")
            if getattr(config, 'PAPER_TRADING', True):
                return self._simulate_order(...)
            else:
                raise TradingDisabledException()
        # ... real order execution
```

Document in README:
```markdown
## Safety Modes

- **PAPER_TRADING=True**: Simulates orders (no broker API called)
- **TRADING_ENABLED=False**: All order methods blocked (fail-safe)
- **TRADING_ENABLED=True + PAPER_TRADING=False**: LIVE TRADING (use only after validation)
```

## Files Changed

✓ [src/utils/options_helper.py](src/utils/options_helper.py)
- Added `if not self.client:` check in `get_option_greeks()` (Bug A1 fixed)
- Updated `compute_offset()` to use config-based STRIKE_STEP (Bug A2 fixed)

✓ [infra/config/base.py](infra/config/base.py)
- Removed hardcoded DATABASE_PASSWORD; require env var in prod

✓ [infra/config/config.py](infra/config/config.py)
- Removed hardcoded DATABASE_PASSWORD; require env var in prod

✓ [Dockerfile](Dockerfile)
- Fixed healthcheck endpoint: /health → /monitor/health (Bug A3 fixed)

✓ [docker-compose.yml](docker-compose.yml)
- Fixed healthcheck endpoint: /health → /monitor/health

## Remaining Actions

| Priority | Task | Owner | Deadline |
|----------|------|-------|----------|
| P0 (Blocker) | Move/merge/remove src/ code; update Dockerfile COPY | DevOps | Before deploy |
| P0 (Safety) | Verify Greeks/OI data source; document decision | Trading | Before live |
| P1 (QA) | Run Test0-Test8 phase tests with app/ imports only | QA | Before release |
| P1 (Docs) | Update README with "canonical package" note | Docs | Before release |
| P2 (Tech debt) | Remove src/ or move to legacy/ folder | DevOps | Next sprint |

## References

- Bug reports: Issue #8 "References"
- Docker issues: [docker-compose.yml](docker-compose.yml) healthcheck mismatch
- Security: [infra/config/config.py](infra/config/config.py) hardcoded secrets
- Code locations:
  - Canonical order execution: [app/domains/trading/order_manager.py](app/domains/trading/order_manager.py)
  - Broker adapter: [app/services/broker/angelone_adapter.py](app/services/broker/angelone_adapter.py)
  - Options data (legacy OpenAlgo): [src/utils/options_helper.py](src/utils/options_helper.py) → should migrate to app/
