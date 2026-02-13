#!/bin/bash
# =============================================================================
# Mission Control v2 - Deploy Script
# =============================================================================
# Usage: ./deploy.sh
# =============================================================================

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Mission Control v2 - Deploy${NC}"
echo -e "${GREEN}========================================${NC}"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

# Check Docker Compose
if ! docker compose version &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not available${NC}"
    exit 1
fi

# Check if infrastructure is running
echo -e "${YELLOW}Checking infrastructure...${NC}"
if ! docker network ls | grep -q "backend"; then
    echo -e "${YELLOW}Creating backend network...${NC}"
    docker network create backend 2>/dev/null || true
fi

# Build and start
echo -e "${GREEN}Building and starting services...${NC}"
docker compose up -d --build

# Wait for services
echo -e "${YELLOW}Waiting for services to start...${NC}"
sleep 5

# Health check
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Checking Services${NC}"
echo -e "${GREEN}========================================${NC}"

# Check backend
if curl -s http://localhost:4000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend API: http://localhost:4000${NC}"
else
    echo -e "${YELLOW}⏳ Backend starting... (may take a moment)${NC}"
fi

# Check frontend
if curl -s http://localhost:4001 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Frontend: http://localhost:4001${NC}"
else
    echo -e "${YELLOW}⏳ Frontend starting... (may take a moment)${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Deploy Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Access Points:"
echo "  Frontend:  http://localhost:4001"
echo "  Backend:   http://localhost:4000"
echo "  API Docs:  http://localhost:4000/docs"
echo ""
echo "View logs: docker compose logs -f"
echo "Stop:      docker compose down"
echo ""
