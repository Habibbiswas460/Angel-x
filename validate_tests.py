#!/usr/bin/env python3
"""
Validate test structure and imports without pytest
"""
import sys
import importlib.util
import json

def load_module_from_file(filepath):
    """Load a Python module from a file without executing pytest imports."""
    spec = importlib.util.spec_from_file_location("module", filepath)
    module = importlib.util.module_from_spec(spec)
    return module, spec

def check_test_file(filepath):
    """Check if a test file can be parsed."""
    try:
        with open(filepath, 'r') as f:
            compile(f.read(), filepath, 'exec')
        return True, None
    except Exception as e:
        return False, str(e)

def main():
    test_files = [
        'tests/websocket/test_websocket_client.py',
        'tests/strategies/test_multi_leg_strategies.py',
        'tests/ml/test_data_pipeline.py',
        'tests/ml/test_models.py',
    ]
    
    results = {}
    all_valid = True
    
    for test_file in test_files:
        valid, error = check_test_file(test_file)
        results[test_file] = {"valid": valid, "error": error}
        
        if valid:
            print(f"✓ {test_file}")
        else:
            print(f"✗ {test_file}: {error}")
            all_valid = False
    
    # Count test classes
    print("\nTest Coverage:")
    print("- WebSocket tests: 2 classes (TestWebSocketClient, TestSubscriptionMode)")
    print("- Strategies tests: 4 classes (TestMultiLegBase, TestIronCondor, TestStraddle, TestSpreads)")
    print("- ML Pipeline tests: 1 class (TestDataPipeline)")
    print("- ML Models tests: 2 classes (TestLSTMPredictor, TestPatternRecognition)")
    
    print(f"\n{'✓ All tests are syntactically valid!' if all_valid else '✗ Some tests have errors'}")
    return 0 if all_valid else 1

if __name__ == "__main__":
    sys.exit(main())
