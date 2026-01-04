#!/bin/bash
# Angel-X Production Setup Script
# Automates installation and configuration

set -e  # Exit on error

echo "============================================"
echo "Angel-X v10.0.0 - Production Setup"
echo "============================================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo "Checking Python version..."
python3 --version

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo ""
    echo "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
    echo "${GREEN}✓ Virtual environment created${NC}"
else
    echo "${GREEN}✓ Virtual environment exists${NC}"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install package in editable mode
echo ""
echo "${YELLOW}Installing Angel-X package...${NC}"
pip install -e .

# Install production dependencies
echo ""
echo "${YELLOW}Installing production dependencies...${NC}"
pip install gunicorn supervisor

# Install dev dependencies (optional)
read -p "Install development tools (pytest, black, mypy)? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "${YELLOW}Installing development tools...${NC}"
    pip install -e .[dev]
fi

# Setup configuration
echo ""
echo "${YELLOW}Setting up configuration...${NC}"

if [ ! -f "config/config.py" ]; then
    cp config/config.example.py config/config.py
    echo "${GREEN}✓ Created config/config.py from template${NC}"
    echo "${YELLOW}⚠ IMPORTANT: Edit config/config.py with your API credentials${NC}"
else
    echo "${GREEN}✓ config/config.py already exists${NC}"
fi

# Create .env if not exists
if [ ! -f ".env" ]; then
    cat > .env << 'EOF'
# Angel-X Environment Configuration
ENV=development
DEBUG=True
SECRET_KEY=change-this-in-production-use-secrets.token_hex-32
ENCRYPTION_ENABLED=False

# Logging
LOG_LEVEL=INFO
MAX_LOG_SIZE_MB=100
BACKUP_COUNT=10
EOF
    echo "${GREEN}✓ Created .env file${NC}"
    echo "${YELLOW}⚠ IMPORTANT: Change SECRET_KEY before production${NC}"
else
    echo "${GREEN}✓ .env already exists${NC}"
fi

# Create required directories
echo ""
echo "Creating required directories..."
mkdir -p logs/archive
mkdir -p data
mkdir -p data/adaptive
echo "${GREEN}✓ Directories created${NC}"

# Display banner
echo ""
python3 -c "from src import print_banner; print_banner()"

# Run verification
echo ""
echo "${YELLOW}Running installation verification...${NC}"
echo ""
python3 scripts/verify_production_setup.py

# Success message
echo ""
echo "${GREEN}============================================${NC}"
echo "${GREEN}Angel-X Setup Complete!${NC}"
echo "${GREEN}============================================${NC}"
echo ""
echo "Next steps:"
echo "1. Activate environment: ${YELLOW}source venv/bin/activate${NC}"
echo "2. Edit configuration: ${YELLOW}nano config/config.py${NC}"
echo "3. Test credentials: ${YELLOW}python3 scripts/test_credentials.py${NC}"
echo "4. Run integration tests: ${YELLOW}python3 scripts/test_adaptive_integration.py${NC}"
echo "5. Start trading: ${YELLOW}python3 main.py${NC}"
echo ""
echo "Dashboard: ${YELLOW}python3 src/dashboard/dashboard.py${NC}"
echo "Or use console script: ${YELLOW}angelx-dashboard${NC}"
echo ""
