#!/bin/bash

################################################################################
# Angel-X Setup Script
# Automated setup for development and production environments
# Usage: bash setup.sh [dev|prod]
################################################################################

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Environment
ENV=${1:-dev}
PYTHON_VERSION="3.11"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║           Angel-X Setup Script - Environment: $ENV           ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"

# ============================================================================
# 1. Check prerequisites
# ============================================================================
echo -e "\n${BLUE}[1/7] Checking prerequisites...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python3 not found. Please install Python 3.8+${NC}"
    exit 1
fi

python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓ Python $python_version found${NC}"

if ! command -v git &> /dev/null; then
    echo -e "${RED}✗ Git not found. Please install Git${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Git found${NC}"

# ============================================================================
# 2. Create virtual environment
# ============================================================================
echo -e "\n${BLUE}[2/7] Creating virtual environment...${NC}"

if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi

source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# ============================================================================
# 3. Upgrade pip
# ============================================================================
echo -e "\n${BLUE}[3/7] Upgrading pip...${NC}"

pip install --upgrade pip setuptools wheel -q
echo -e "${GREEN}✓ Pip upgraded${NC}"

# ============================================================================
# 4. Install dependencies
# ============================================================================
echo -e "\n${BLUE}[4/7] Installing dependencies...${NC}"

pip install -r requirements.txt -q
echo -e "${GREEN}✓ Main dependencies installed${NC}"

if [ "$ENV" = "dev" ] || [ "$ENV" = "development" ]; then
    pip install -r requirements-test.txt -q
    echo -e "${GREEN}✓ Development dependencies installed${NC}"
fi

# ============================================================================
# 5. Setup environment configuration
# ============================================================================
echo -e "\n${BLUE}[5/7] Setting up configuration...${NC}"

if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✓ .env file created from .env.example${NC}"
    else
        cat > .env <<'EOF'
# Angel-X environment configuration
# Populate with your secrets before running in real mode
ANGELONE_API_KEY=
ANGELONE_CLIENT_CODE=
ANGELONE_PASSWORD=
ANGELONE_TOTP_SECRET=
EOF
        echo -e "${GREEN}✓ .env file created (blank stub)${NC}"
    fi
    echo -e "${RED}  ⚠ Edit .env with your AngelOne credentials!${NC}"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

# ============================================================================
# 6. Setup pre-commit hooks (dev only)
# ============================================================================
echo -e "\n${BLUE}[6/7] Setting up development tools...${NC}"

if [ "$ENV" = "dev" ] || [ "$ENV" = "development" ]; then
    if [ -f ".pre-commit-config.yaml" ]; then
        pip install pre-commit -q
        pre-commit install
        echo -e "${GREEN}✓ Pre-commit hooks installed${NC}"
    fi
fi

# ============================================================================
# 7. Verify installation
# ============================================================================
echo -e "\n${BLUE}[7/7] Verifying installation...${NC}"

python -c "
import sys
print(f'✓ Python executable: {sys.executable}')
print(f'✓ Python version: {sys.version.split()[0]}')
"

# Test imports
python -c "
try:
    import flask
    print('✓ Flask imported successfully')
except ImportError as e:
    print(f'✗ Error importing Flask: {e}')
"

# ============================================================================
# Summary
# ============================================================================
echo -e "\n${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}✓ Setup completed successfully!${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"

echo -e "\n${BLUE}Next steps:${NC}"
echo -e "  1. Edit .env with your AngelOne credentials"
echo -e "  2. Start application: python main.py"
echo -e "  3. Visit dashboard: http://localhost:5000"

if [ "$ENV" = "dev" ] || [ "$ENV" = "development" ]; then
    echo -e "  4. Run tests: pytest tests/ -v"
    echo -e "  5. Format code: black src/ tests/"
fi

echo -e "\n${BLUE}Documentation:${NC}"
echo -e "  • README.md - Project overview"
echo -e "  • INSTALLATION.md - Detailed setup"
echo -e "  • docs/FAQ.md - Common questions"

echo -e "\n${GREEN}Happy trading! 🚀${NC}\n"
