#!/bin/bash
# Quick test runner scripts

# Test progress
alias test-progress='python3 scripts/run_master_test.py --progress'

# Individual tests
alias test-0='python3 scripts/run_master_test.py --test TEST-0'
alias test-1='python3 scripts/run_master_test.py --test TEST-1'
alias test-2='python3 scripts/run_master_test.py --test TEST-2'
alias test-3='python3 scripts/run_master_test.py --test TEST-3'
alias test-4='python3 scripts/run_master_test.py --test TEST-4'
alias test-5='python3 scripts/run_master_test.py --test TEST-5'
alias test-6='python3 scripts/run_master_test.py --test TEST-6'
alias test-7='python3 scripts/run_master_test.py --test TEST-7'
alias test-8='python3 scripts/run_master_test.py --test TEST-8'

# Run all tests
alias test-all='python3 scripts/run_master_test.py --auto'

echo "Test aliases loaded:"
echo "  test-progress  - Show current progress"
echo "  test-0 to test-8  - Run specific test"
echo "  test-all  - Run all tests in sequence"
