#!/bin/bash

# AI Platform - Logs Script
# View logs from all or specific services

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Determine docker-compose command (plugin or standalone)
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

# Change to script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Help message
show_help() {
    echo "AI Platform - Logs Viewer"
    echo ""
    echo "Usage: $0 [options] [service]"
    echo ""
    echo "Options:"
    echo "  -f, --follow      Follow log output (like tail -f)"
    echo "  --tail N          Show last N lines (default: 100)"
    echo "  --timestamps      Show timestamps"
    echo "  -h, --help        Show this help message"
    echo ""
    echo "Services:"
    echo "  postgres, redis, chromadb, backend, frontend, ollama, nginx"
    echo "  (or 'all' to show all logs)"
    echo ""
    echo "Examples:"
    echo "  $0                    # Show all recent logs"
    echo "  $0 -f                 # Follow all logs"
    echo "  $0 backend            # Show backend logs only"
    echo "  $0 -f backend         # Follow backend logs"
    echo "  $0 --tail 500 backend # Show last 500 lines of backend logs"
}

# Default values
FOLLOW=false
TAIL=100
SHOW_TIMESTAMPS=false
SERVICE=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--follow)
            FOLLOW=true
            shift
            ;;
        --tail)
            TAIL="$2"
            shift 2
            ;;
        --timestamps)
            SHOW_TIMESTAMPS=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            if [ -z "$SERVICE" ]; then
                SERVICE="$1"
            else
                echo -e "${RED}Unknown option: $1${NC}"
                show_help
                exit 1
            fi
            shift
            ;;
    esac
done

# Build docker compose command
CMD="$DOCKER_COMPOSE -f docker-compose.yml logs"

# Add options
if [ "$FOLLOW" = true ]; then
    CMD="$CMD --follow"
fi

if [ "$TAIL" != "0" ]; then
    CMD="$CMD --tail $TAIL"
fi

if [ "$SHOW_TIMESTAMPS" = true ]; then
    CMD="$CMD --timestamps"
fi

# Add service if specified
if [ -n "$SERVICE" ]; then
    # Map service names
    case "$SERVICE" in
        all)
            # All logs
            ;;
        postgres|postgresql|db)
            SERVICE="postgres"
            ;;
        redis|cache)
            SERVICE="redis"
            ;;
        chromadb|chroma|vector)
            SERVICE="chromadb"
            ;;
        backend|api|fastapi)
            SERVICE="backend"
            ;;
        frontend|next|nextjs)
            SERVICE="frontend"
            ;;
        ollama|llm)
            SERVICE="ollama"
            ;;
        nginx|proxy)
            SERVICE="nginx"
            ;;
        *)
            echo -e "${RED}Unknown service: $SERVICE${NC}"
            echo "Valid services: postgres, redis, chromadb, backend, frontend, ollama, nginx"
            exit 1
            ;;
    esac
    CMD="$CMD $SERVICE"
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   AI Platform - Viewing Logs          ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Show header based on service
if [ -z "$SERVICE" ]; then
    echo -e "${CYAN}Showing logs from all services${NC}"
elif [ "$SERVICE" = "all" ]; then
    echo -e "${CYAN}Showing logs from all services${NC}"
else
    echo -e "${CYAN}Showing logs from: ${YELLOW}$SERVICE${NC}"
fi

echo ""

# Execute command
exec $CMD
