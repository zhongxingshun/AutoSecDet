#!/bin/bash

# AutoSecDet Docker Compose Startup Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  AutoSecDet - Starting Services${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Warning: .env file not found. Creating from .env.example...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}Please update .env with your production settings!${NC}"
fi

# Build and start services
echo -e "\n${GREEN}Building and starting containers...${NC}"
docker-compose up -d --build

# Wait for services to be healthy
echo -e "\n${GREEN}Waiting for services to be healthy...${NC}"
sleep 10

# Check service status
echo -e "\n${GREEN}Checking service status...${NC}"
docker-compose ps

# Run database migrations
echo -e "\n${GREEN}Running database migrations...${NC}"
docker-compose exec -T backend alembic upgrade head || echo -e "${YELLOW}Migration may have already been applied${NC}"

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  AutoSecDet is now running!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e ""
echo -e "  API:      http://localhost:8000"
echo -e "  API Docs: http://localhost:8000/docs"
echo -e "  Health:   http://localhost:8000/api/v1/health"
echo -e ""
echo -e "  Default admin credentials:"
echo -e "    Username: admin"
echo -e "    Password: admin123"
echo -e ""
echo -e "${YELLOW}  ⚠️  Please change the default password!${NC}"
echo -e ""
