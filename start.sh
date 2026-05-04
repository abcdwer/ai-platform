#!/bin/bash

# AI Platform - Start Script
# Starts all services using Docker Compose

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   AI Platform - Starting Services     ${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if docker-compose or docker compose plugin is available
if ! docker compose version &> /dev/null && ! docker-compose --version &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# Determine docker-compose command (plugin or standalone)
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

# Change to script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check for .env file (docker-compose.yml uses ./backend/.env)
if [ ! -f "./backend/.env" ]; then
    echo -e "${YELLOW}Warning: backend/.env file not found${NC}"
    echo "Creating backend/.env from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example ./backend/.env
        echo -e "${YELLOW}Please edit ./backend/.env with your configuration${NC}"
    fi
fi

# Parse command line arguments
COMPOSE_FILE="-f docker-compose.yml"
START_OLLAMA=false
BUILD=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --ollama)
            START_OLLAMA=true
            echo -e "${YELLOW}Ollama service will be started${NC}"
            shift
            ;;
        --build)
            BUILD=true
            echo -e "${YELLOW}Images will be rebuilt${NC}"
            shift
            ;;
        --local)
            COMPOSE_FILE="$COMPOSE_FILE -f docker-compose.local.yml"
            echo -e "${YELLOW}Using local development configuration${NC}"
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Usage: $0 [--ollama] [--build] [--local]"
            exit 1
            ;;
    esac
done

# Build images if requested
if [ "$BUILD" = true ]; then
    echo -e "\n${YELLOW}Building Docker images...${NC}"
    $DOCKER_COMPOSE $COMPOSE_FILE build --no-cache
fi

# Start services
echo -e "\n${YELLOW}Starting services...${NC}"
$DOCKER_COMPOSE $COMPOSE_FILE up -d

# Wait for services to be healthy
echo -e "\n${YELLOW}Waiting for services to be ready...${NC}"
sleep 5

# Check service status
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}   Service Status                       ${NC}"
echo -e "${GREEN}========================================${NC}"
$DOCKER_COMPOSE $COMPOSE_FILE ps

# Display access URLs
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}   Access URLs                          ${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "Frontend:    ${YELLOW}http://localhost:3000${NC}"
echo -e "Backend API: ${YELLOW}http://localhost:8000${NC}"
echo -e "API Docs:    ${YELLOW}http://localhost:8000/docs${NC}"
echo -e "ChromaDB:    ${YELLOW}http://localhost:8001${NC}"
echo -e "PostgreSQL:  ${YELLOW}localhost:5432${NC}"
echo -e "Redis:       ${YELLOW}localhost:6379${NC}"

# Check Ollama if started
if [ "$START_OLLAMA" = true ]; then
    echo -e "Ollama:      ${YELLOW}http://localhost:11434${NC}"
fi

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}   AI Platform is running!             ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "View logs: $0 logs"
echo "Stop services: ./stop.sh"
echo ""
