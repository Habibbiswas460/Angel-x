#!/bin/bash
# Setup development environment for Angel-X

set -e

echo "🚀 Setting up Angel-X development environment..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python version: $python_version"

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate
echo "✅ Virtual environment activated"

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install requirements
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Setup database
if command -v psql &> /dev/null; then
    echo "✅ PostgreSQL found"
    echo "📦 Setting up database..."
    bash tools/scripts/setup_db.sh
else
    echo "⚠️  PostgreSQL not found. Install it and run: bash tools/scripts/setup_db.sh"
fi

# Create necessary directories
mkdir -p logs/{trades,metrics,reports}
mkdir -p data

# Run tests
echo "📦 Running test suite..."
python -m pytest tests/unit -v --tb=short || true

echo "✅ Development environment setup complete!"
echo ""
echo "Next steps:"
echo "  1. Configure your .env file with API credentials"
echo "  2. Run: python main.py"
echo "  3. Open: http://localhost:5000"
