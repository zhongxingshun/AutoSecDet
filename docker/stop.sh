#!/bin/bash

# AutoSecDet Docker Compose Stop Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  AutoSecDet - Stopping Services${NC}"
echo -e "${GREEN}========================================${NC}"

docker-compose down

echo -e "\n${GREEN}All services stopped.${NC}"
echo -e ""
echo -e "To remove volumes (delete all data), run:"
echo -e "  docker-compose down -v"
echo -e ""
