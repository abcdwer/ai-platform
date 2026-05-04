#!/bin/bash

# AI Platform - Stop Script
# Stops all services and optionally removes volumes

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   AI Platform - Stopping Services    ${NC}"
echo -e "${GREEN}========================================${NC}"

# Determine docker-compose command (plugin or standalone)
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

# Change to script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Parse command line arguments
REMOVE_VOLUMES=false
REMOVE_IMAGES=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--volumes)
            REMOVE_VOLUMES=true
            echo -e "${YELLOW}Volumes will be removed (data loss!)${NC}"
            shift
            ;;
        --images)
            REMOVE_IMAGES=true
            echo -e "${YELLOW}Images will be removed${NC}"
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [-v|--volumes] [--images]"
            echo ""
            echo "Options:"
            echo "  -v, --volumes   Remove data volumes (WARNING: all data will be lost!)"
            echo "  --images        Remove Docker images"
            echo "  -h, --help      Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Stop services
echo -e "\n${YELLOW}Stopping services...${NC}"
$DOCKER_COMPOSE -f docker-compose.yml down

# Remove volumes if requested
if [ "$REMOVE_VOLUMES" = true ]; then
    echo -e "\n${YELLOW}Removing data volumes...${NC}"
    $DOCKER_COMPOSE -f docker-compose.yml down -v
    
    # Also remove any named volumes
    docker volume rm ai-platform_postgres_data 2>/dev/null || true
    docker volume rm ai-platform_redis_data 2>/dev/null || true
    docker volume rm ai-platform_chromadb_data 2>/dev/null || true
fi

# Remove images if requested
if [ "$REMOVE_IMAGES" = true ]; then
    echo -e "\n${YELLOW}Removing images...${NC}"
    docker rmi ai-platform-backend 2>/dev/null || true
    docker rmi ai-platform-frontend 2>/dev/null || true
fi

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}   All services stopped                 ${NC}"
echo -e "${GREEN}========================================${NC}"

if [ "$REMOVE_VOLUMES" = true ]; then
    echo -e "${YELLOW}Warning: All data has been deleted!${NC}"
fi
