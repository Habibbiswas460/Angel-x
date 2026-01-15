#!/bin/bash
# Docker deployment script for Angel-X

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "================================================================================"
echo -e "${BLUE}  🐳 ANGEL-X DOCKER DEPLOYMENT${NC}"
echo "================================================================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found${NC}"
    echo "Would you like to create .env from .env.docker template? (y/n)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        cp .env.docker .env
        echo -e "${GREEN}✅ Created .env file${NC}"
        echo -e "${YELLOW}⚠️  Please edit .env and add your credentials before continuing${NC}"
        exit 0
    else
        echo -e "${RED}❌ Cannot proceed without .env file${NC}"
        exit 1
    fi
fi

# Parse command line arguments
MODE=${1:-"up"}

case $MODE in
    "up")
        echo -e "${BLUE}📦 Starting Angel-X services...${NC}"
        docker-compose up -d
        echo ""
        echo -e "${GREEN}✅ Services started${NC}"
        echo ""
        docker-compose ps
        ;;
        
    "up-monitoring")
        echo -e "${BLUE}📦 Starting Angel-X with monitoring stack...${NC}"
        docker-compose --profile monitoring up -d
        echo ""
        echo -e "${GREEN}✅ Services started with monitoring${NC}"
        echo ""
        docker-compose ps
        ;;
        
    "down")
        echo -e "${BLUE}🛑 Stopping Angel-X services...${NC}"
        docker-compose down
        echo -e "${GREEN}✅ Services stopped${NC}"
        ;;
        
    "restart")
        echo -e "${BLUE}🔄 Restarting Angel-X services...${NC}"
        docker-compose restart
        echo -e "${GREEN}✅ Services restarted${NC}"
        ;;
        
    "logs")
        echo -e "${BLUE}📋 Showing logs...${NC}"
        docker-compose logs -f
        ;;
        
    "build")
        echo -e "${BLUE}🔨 Building Angel-X image...${NC}"
        docker-compose build --no-cache
        echo -e "${GREEN}✅ Build complete${NC}"
        ;;
        
    "init-db")
        echo -e "${BLUE}🗄️  Initializing database...${NC}"
        docker-compose exec angel-x python init_db.py
        echo -e "${GREEN}✅ Database initialized${NC}"
        ;;
        
    "validate")
        echo -e "${BLUE}✓ Validating configuration...${NC}"
        docker-compose exec angel-x python validate_config.py
        ;;
        
    "shell")
        echo -e "${BLUE}🐚 Opening shell in Angel-X container...${NC}"
        docker-compose exec angel-x bash
        ;;
        
    "status")
        echo -e "${BLUE}📊 Service Status:${NC}"
        echo ""
        docker-compose ps
        echo ""
        echo -e "${BLUE}📊 Container Stats:${NC}"
        echo ""
        docker stats --no-stream
        ;;
        
    "clean")
        echo -e "${YELLOW}⚠️  This will remove all containers and volumes (data will be lost)${NC}"
        echo "Are you sure? (yes/no)"
        read -r response
        if [[ "$response" == "yes" ]]; then
            echo -e "${BLUE}🗑️  Cleaning up...${NC}"
            docker-compose down -v
            echo -e "${GREEN}✅ Cleanup complete${NC}"
        else
            echo -e "${BLUE}Cancelled${NC}"
        fi
        ;;
        
    "backup")
        echo -e "${BLUE}💾 Creating backup...${NC}"
        TIMESTAMP=$(date +%Y%m%d_%H%M%S)
        BACKUP_DIR="backups/$TIMESTAMP"
        mkdir -p "$BACKUP_DIR"
        
        # Backup database
        docker-compose exec -T postgres pg_dump -U angelx angel_x > "$BACKUP_DIR/database.sql"
        
        # Backup volumes
        tar -czf "$BACKUP_DIR/data.tar.gz" data/ logs/ models/ 2>/dev/null || true
        
        echo -e "${GREEN}✅ Backup saved to $BACKUP_DIR${NC}"
        ;;
        
    *)
        echo "Usage: $0 {up|up-monitoring|down|restart|logs|build|init-db|validate|shell|status|clean|backup}"
        echo ""
        echo "Commands:"
        echo "  up              - Start services"
        echo "  up-monitoring   - Start services with Prometheus & Grafana"
        echo "  down            - Stop services"
        echo "  restart         - Restart services"
        echo "  logs            - View logs"
        echo "  build           - Build Docker image"
        echo "  init-db         - Initialize database"
        echo "  validate        - Validate configuration"
        echo "  shell           - Open bash shell"
        echo "  status          - Show service status"
        echo "  clean           - Remove all containers and volumes"
        echo "  backup          - Backup database and data"
        exit 1
        ;;
esac

echo ""
echo -e "${BLUE}================================================================================${NC}"
echo -e "${GREEN}✅ Done!${NC}"
echo -e "${BLUE}================================================================================${NC}"

# Show access URLs
if [[ $MODE == "up" ]] || [[ $MODE == "up-monitoring" ]]; then
    echo ""
    echo -e "${BLUE}📱 Access URLs:${NC}"
    echo "  Dashboard: http://localhost:5001"
    echo "  API:       http://localhost:5000"
    if [[ $MODE == "up-monitoring" ]]; then
        echo "  Grafana:   http://localhost:3000 (admin/admin)"
        echo "  Prometheus: http://localhost:9090"
    fi
    echo ""
fi
