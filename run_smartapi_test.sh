#!/bin/bash
# Run SmartAPI integration test

# Activate environment if needed
# source venv/bin/activate

# Set paper trading mode
export PAPER_TRADING=True

# Run test
python3 scripts/test_smartapi_integration.py
