#!/usr/bin/env python
"""
ANGEL-X Professional Test Runner
Quick execution and reporting
"""

import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent

def run_tests(test_type="all", verbose=False, coverage=False):
    """Run tests with specified parameters"""
    
    cmd = ["pytest"]
    
    if test_type == "unit":
        cmd.extend(["tests/unit/", "-m", "unit"])
        print("🧪 Running UNIT TESTS (fast)...")
    elif test_type == "integration":
        cmd.extend(["tests/integration/", "-m", "integration"])
        print("🔗 Running INTEGRATION TESTS...")
    elif test_type == "e2e":
        cmd.extend(["tests/e2e/", "-m", "e2e"])
        print("🎯 Running END-TO-END TESTS...")
    elif test_type == "smoke":
        cmd.extend(["-m", "smoke"])
        print("💨 Running SMOKE TESTS...")
    else:
        cmd.append("tests/")
        print("📊 Running ALL TESTS...")
    
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")
    
    if coverage:
        cmd.extend(["--cov=src", "--cov-report=term-missing", "--cov-report=html"])
        print("📈 Coverage report will be in htmlcov/index.html")
    
    cmd.append("--tb=short")
    
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    return result.returncode


def main():
    """Main entry point"""
    test_type = "all"
    verbose = False
    coverage = False
    
    if len(sys.argv) > 1:
        test_type = sys.argv[1]
    if "--verbose" in sys.argv or "-v" in sys.argv:
        verbose = True
    if "--coverage" in sys.argv or "-c" in sys.argv:
        coverage = True
    
    print("=" * 70)
    print("ANGEL-X TEST SUITE")
    print("=" * 70)
    
    exit_code = run_tests(test_type, verbose, coverage)
    
    print("=" * 70)
    if exit_code == 0:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ TESTS FAILED")
    print("=" * 70)
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
