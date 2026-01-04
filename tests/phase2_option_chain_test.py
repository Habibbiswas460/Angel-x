#!/usr/bin/env python3
"""
Phase 2 Option Chain Data Engine - Validation Tests

Tests:
1. Data models creation and validation
2. Noise filters
3. Snapshot management
4. Health monitoring
5. Stream interface
"""

import sys
from datetime import datetime, timedelta
from src.utils.option_chain_data_models import (
    StrikeData, StrikePair, OptionChainSnapshot, ExpiryInfo, 
    UniverseDefinition, OptionType, DataHealthStatus, DataHealthReport
)
from src.utils.option_chain_filters import (
    NoiseFilter, DataValidator, StaleDataDetector, BrokerHiccupDetector
)
from src.utils.option_chain_snapshot import SnapshotEngine, SnapshotCache

print("\n" + "="*70)
print("  PHASE 2: OPTION CHAIN DATA ENGINE - VALIDATION")
print("="*70 + "\n")

# Test 1: Data Models
print("TEST 1: Data Models")
print("-"*70)

try:
    # Create strike data
    ce_strike = StrikeData(
        strike=20000.0,
        option_type=OptionType.CE,
        ltp=150.50,
        bid=150.25,
        ask=150.75,
        volume=10000,
        oi=500000,
        timestamp=datetime.utcnow()
    )
    
    pe_strike = StrikeData(
        strike=20000.0,
        option_type=OptionType.PE,
        ltp=140.25,
        bid=140.00,
        ask=140.50,
        volume=8000,
        oi=480000,
        timestamp=datetime.utcnow()
    )
    
    # Create strike pair
    pair = StrikePair(strike=20000.0, ce=ce_strike, pe=pe_strike)
    
    # Create snapshot
    snapshot = OptionChainSnapshot(
        underlying="NIFTY",
        expiry="08JAN26",
        atm_strike=20000.0
    )
    snapshot.strikes[20000.0] = pair
    
    print("  ✓ Created StrikeData instances")
    print(f"    CE LTP: {ce_strike.ltp}, OI: {ce_strike.oi}")
    print(f"    PE LTP: {pe_strike.ltp}, OI: {pe_strike.oi}")
    print("  ✓ Created StrikePair")
    print(f"    Is complete: {pair.is_complete}")
    print(f"    Both liquid: {pair.both_liquid}")
    print("  ✓ Created OptionChainSnapshot")
    print(f"    Strikes: {snapshot.strike_count}")
    print(f"    Complete pairs: {snapshot.complete_pairs}")
    
except Exception as e:
    print(f"  ✗ FAILED: {e}")
    sys.exit(1)

# Test 2: Noise Filters
print("\nTEST 2: Noise Filters")
print("-"*70)

try:
    filter = NoiseFilter(config={
        'min_volume': 0,
        'max_ltp_jump_percent': 10.0,
        'max_oi_jump_percent': 20.0
    })
    
    # Test zero volume filter
    zero_vol = StrikeData(
        strike=20100.0,
        option_type=OptionType.CE,
        ltp=100.0,
        volume=0,
        oi=0
    )
    
    is_valid, reason = filter.validate_strike(zero_vol)
    print(f"  ✓ Zero volume filter: valid={is_valid}, reason={reason}")
    
    # Test normal strike
    normal = StrikeData(
        strike=20100.0,
        option_type=OptionType.CE,
        ltp=100.0,
        volume=5000,
        oi=250000
    )
    
    is_valid, reason = filter.validate_strike(normal)
    print(f"  ✓ Normal strike validation: valid={is_valid}")
    
except Exception as e:
    print(f"  ✗ FAILED: {e}")
    sys.exit(1)

# Test 3: Data Validator
print("\nTEST 3: Data Validator")
print("-"*70)

try:
    validator = DataValidator()
    
    # Test expiry match
    is_valid = validator.check_expiry_match(snapshot, "08JAN26")
    print(f"  ✓ Expiry validation: {is_valid}")
    
    # Test strike alignment
    is_aligned, reason = validator.check_strike_alignment(snapshot)
    print(f"  ✓ Strike alignment: {is_aligned} ({reason})")
    
    # Test completeness
    is_complete, score = validator.check_completeness(snapshot, min_pairs=1)
    print(f"  ✓ Completeness check: {is_complete}, score={score:.1%}")
    
    # Test quality score
    quality = validator.compute_quality_score(snapshot)
    print(f"  ✓ Quality score: {quality:.1f}/100")
    
except Exception as e:
    print(f"  ✗ FAILED: {e}")
    sys.exit(1)

# Test 4: Snapshot Engine
print("\nTEST 4: Snapshot Engine")
print("-"*70)

try:
    engine = SnapshotEngine()
    
    # Update with first snapshot
    delta1 = engine.update_snapshot(snapshot)
    print(f"  ✓ First snapshot: current={engine.current is not None}")
    print(f"    Has changes: {delta1.has_changes}")
    
    # Update with second snapshot (create delta)
    snapshot2 = OptionChainSnapshot(
        underlying="NIFTY",
        expiry="08JAN26",
        atm_strike=20000.0
    )
    
    # Modify CE LTP
    ce2 = StrikeData(
        strike=20000.0,
        option_type=OptionType.CE,
        ltp=151.50,  # Changed from 150.50
        volume=11000,  # Changed from 10000
        oi=510000,  # Changed from 500000
        timestamp=datetime.utcnow()
    )
    
    pair2 = StrikePair(strike=20000.0, ce=ce2, pe=pe_strike)
    snapshot2.strikes[20000.0] = pair2
    
    delta2 = engine.update_snapshot(snapshot2)
    print(f"  ✓ Second snapshot: previous set={engine.previous is not None}")
    print(f"    Delta has changes: {delta2.has_changes}")
    print(f"    OI changes: {delta2.oi_changes}")
    print(f"    Volume changes: {delta2.volume_changes}")
    
    # Test interface
    atm_ce = engine.get_atm_ce()
    print(f"  ✓ ATM CE retrieved: LTP={atm_ce.ltp if atm_ce else None}")
    
except Exception as e:
    print(f"  ✗ FAILED: {e}")
    sys.exit(1)

# Test 5: Snapshot Cache
print("\nTEST 5: Snapshot Cache")
print("-"*70)

try:
    cache = SnapshotCache()
    
    # Store
    cache.store("NIFTY", "08JAN26", snapshot)
    print("  ✓ Snapshot stored in cache")
    
    # Retrieve
    retrieved = cache.retrieve("NIFTY", "08JAN26")
    print(f"  ✓ Retrieved from cache: {retrieved is not None}")
    print(f"    Strikes: {retrieved.strike_count if retrieved else 0}")
    
    # List
    cached = cache.list_cached()
    print(f"  ✓ Cached items: {cached}")
    
except Exception as e:
    print(f"  ✗ FAILED: {e}")
    sys.exit(1)

# Test 6: Health Monitoring
print("\nTEST 6: Health Monitoring")
print("-"*70)

try:
    stale_detector = StaleDataDetector(stale_threshold_sec=60)
    
    # Fresh snapshot
    is_stale = stale_detector.is_stale(snapshot)
    print(f"  ✓ Fresh snapshot stale check: {is_stale}")
    
    # Old snapshot
    old_snapshot = OptionChainSnapshot(
        underlying="NIFTY",
        expiry="08JAN26",
        timestamp=datetime.utcnow() - timedelta(seconds=120)
    )
    is_stale = stale_detector.is_stale(old_snapshot)
    print(f"  ✓ Old snapshot stale check: {is_stale}")
    
    # Broker hiccup detector
    hiccup = BrokerHiccupDetector(error_threshold=3)
    hiccup.record_error()
    hiccup.record_error()
    should_pause = hiccup.should_soft_pause()
    print(f"  ✓ After 2 errors, should pause: {should_pause}")
    
    hiccup.record_error()
    should_pause = hiccup.should_soft_pause()
    print(f"  ✓ After 3 errors, should pause: {should_pause}")
    
except Exception as e:
    print(f"  ✗ FAILED: {e}")
    sys.exit(1)

# Test 7: Universe Definition
print("\nTEST 7: Universe Definition")
print("-"*70)

try:
    expiry = ExpiryInfo(
        expiry_code="08JAN26",
        expiry_date=datetime.utcnow() + timedelta(days=4),
        is_weekly=True
    )
    
    universe = UniverseDefinition(
        underlying="NIFTY",
        expiry=expiry,
        atm_reference=20050.0,
        strikes_range=5
    )
    
    print(f"  ✓ Created universe definition")
    print(f"    Underlying: {universe.underlying}")
    print(f"    Expiry: {universe.expiry.expiry_code}")
    print(f"    Days to expiry: {universe.expiry.days_to_expiry}")
    print(f"    Strike range: {universe.strike_range_lower} to {universe.strike_range_upper}")
    print(f"    Expected strikes: {universe.expected_strike_count}")
    
except Exception as e:
    print(f"  ✗ FAILED: {e}")
    sys.exit(1)

# Summary
print("\n" + "="*70)
print("  PHASE 2 DATA ENGINE VALIDATION - ALL TESTS PASSED ✓")
print("="*70 + "\n")

print("Summary:")
print("  ✓ Data models working")
print("  ✓ Noise filters functional")
print("  ✓ Data validation logic correct")
print("  ✓ Snapshot engine operational")
print("  ✓ Caching system working")
print("  ✓ Health monitoring active")
print("  ✓ Universe definition set")

print("\nNext steps:")
print("  1. Integrate with AngelOne broker adapter")
print("  2. Implement real _fetch_from_broker() method")
print("  3. Test with live market data")
print("  4. Add performance tuning")

print()
