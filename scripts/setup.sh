#!/bin/bash
# ===========================================
# Witmind Platform Setup Script
# ===========================================
# This script sets up Witmind on a fresh Ubuntu server
# Run: ./scripts/setup.sh
# ===========================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                  WITMIND SETUP                            ║"
echo "║            AI Agent Platform Installation                 ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
WITMIND_DIR="$(dirname "$SCRIPT_DIR")"
HOME_DIR="$HOME"

echo "Installation directory: $WITMIND_DIR"
echo ""

# ===========================================
# Step 1: Create directories
# ===========================================
echo -e "${YELLOW}[1/6] Creating directories...${NC}"

mkdir -p "$HOME_DIR/witmind-data/projects"
mkdir -p "$HOME_DIR/witmind-data/logs"
mkdir -p "$HOME_DIR/witmind-data/cache"
mkdir -p "$HOME_DIR/workspace"
mkdir -p "$HOME_DIR/bin"

echo "  ✓ Created ~/witmind-data/"
echo "  ✓ Created ~/workspace/"
echo "  ✓ Created ~/bin/"

# ===========================================
# Step 2: Setup Python environment
# ===========================================
echo -e "${YELLOW}[2/6] Setting up Python environment...${NC}"

if [ ! -d "$WITMIND_DIR/.venv" ]; then
    python3 -m venv "$WITMIND_DIR/.venv"
    echo "  ✓ Created virtual environment"
else
    echo "  ✓ Virtual environment already exists"
fi

# Activate venv and install dependencies
source "$WITMIND_DIR/.venv/bin/activate"
pip install --upgrade pip -q

if [ -f "$WITMIND_DIR/cli/requirements.txt" ]; then
    pip install -r "$WITMIND_DIR/cli/requirements.txt" -q
    echo "  ✓ Installed CLI dependencies"
fi

if [ -f "$WITMIND_DIR/platform/requirements.txt" ]; then
    pip install -r "$WITMIND_DIR/platform/requirements.txt" -q
    echo "  ✓ Installed platform dependencies"
fi

# ===========================================
# Step 3: Install wit CLI
# ===========================================
echo -e "${YELLOW}[3/6] Installing wit CLI...${NC}"

# Create wrapper script
cat > "$HOME_DIR/bin/wit" << 'EOF'
#!/bin/bash
# Witmind CLI wrapper
source ~/witmind/.venv/bin/activate
python ~/witmind/cli/wit.py "$@"
EOF

chmod +x "$HOME_DIR/bin/wit"
echo "  ✓ Installed wit command to ~/bin/wit"

# Add ~/bin to PATH if not already
if ! grep -q 'export PATH="$HOME/bin:$PATH"' "$HOME_DIR/.bashrc"; then
    echo 'export PATH="$HOME/bin:$PATH"' >> "$HOME_DIR/.bashrc"
    echo "  ✓ Added ~/bin to PATH"
fi

# ===========================================
# Step 4: Setup environment file
# ===========================================
echo -e "${YELLOW}[4/6] Setting up environment...${NC}"

if [ ! -f "$HOME_DIR/.env" ]; then
    cp "$WITMIND_DIR/.env.example" "$HOME_DIR/.env"
    echo "  ✓ Created ~/.env from template"
    echo -e "  ${RED}⚠ IMPORTANT: Edit ~/.env with your API keys!${NC}"
else
    echo "  ✓ ~/.env already exists"
fi

# ===========================================
# Step 5: Setup Docker network
# ===========================================
echo -e "${YELLOW}[5/6] Setting up Docker...${NC}"

if command -v docker &> /dev/null; then
    docker network create backend 2>/dev/null || true
    echo "  ✓ Docker network 'backend' ready"
else
    echo "  ⚠ Docker not found. Install Docker to run services."
fi

# ===========================================
# Step 6: Verify installation
# ===========================================
echo -e "${YELLOW}[6/6] Verifying installation...${NC}"

# Source bashrc to get PATH
export PATH="$HOME_DIR/bin:$PATH"

# Test wit command
if "$HOME_DIR/bin/wit" --version &> /dev/null; then
    echo "  ✓ wit CLI working"
else
    echo "  ⚠ wit CLI test failed"
fi

# ===========================================
# Done!
# ===========================================
echo ""
echo -e "${GREEN}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                 SETUP COMPLETE!                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo "Next steps:"
echo ""
echo "  1. Edit ~/.env with your API keys:"
echo "     nano ~/.env"
echo ""
echo "  2. Reload shell:"
echo "     source ~/.bashrc"
echo ""
echo "  3. Start Docker services:"
echo "     cd ~/witmind/docker && docker compose up -d"
echo ""
echo "  4. Test wit CLI:"
echo "     wit --help"
echo "     wit status"
echo ""
echo -e "${YELLOW}For more info: https://github.com/6amdev/witmind${NC}"
echo ""
