#!/bin/bash

# ============================================================================
# Podman Setup and Deployment Script
# Automated deployment for Insurance RAG Application using Podman
# ============================================================================

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
print_info "Checking prerequisites..."

if ! command_exists podman; then
    print_error "Podman is not installed. Please install Podman first."
    print_info "Install on Ubuntu/Debian: sudo apt-get install podman"
    print_info "Install on macOS: brew install podman"
    exit 1
fi

if ! command_exists podman-compose; then
    print_warn "podman-compose not found. Attempting to install..."
    if command_exists pip3; then
        pip3 install podman-compose
    else
        print_error "pip3 not found. Please install podman-compose manually."
        exit 1
    fi
fi

print_info "✓ Podman version: $(podman --version)"
print_info "✓ Podman Compose version: $(podman-compose --version)"

# Create required directories
print_info "Creating required directories..."
mkdir -p data/postgres data/app logs
print_info "✓ Directories created"

# Check for .env file
if [ ! -f .env ]; then
    print_warn ".env file not found. Creating template..."
    cat > .env << EOF
GOOGLE_API_KEY=your-api-key-here
POSTGRES_PASSWORD=postgres123
EOF
    print_warn "Please edit .env file and add your GOOGLE_API_KEY"
    exit 1
fi

# Validate GOOGLE_API_KEY
source .env
if [ "$GOOGLE_API_KEY" = "your-api-key-here" ] || [ -z "$GOOGLE_API_KEY" ]; then
    print_error "GOOGLE_API_KEY not set in .env file"
    exit 1
fi

print_info "✓ Environment configuration validated"

# Set proper permissions for rootless Podman
print_info "Setting up permissions for rootless containers..."
if [ "$(id -u)" -ne 0 ]; then
    # Rootless mode
    podman unshare chown -R 1001:1001 data/app logs 2>/dev/null || true
    podman unshare chown -R 999:999 data/postgres 2>/dev/null || true
else
    # Rootful mode
    chown -R 1001:1001 data/app logs
    chown -R 999:999 data/postgres
fi
print_info "✓ Permissions configured"

# Function to cleanup existing containers
cleanup() {
    print_info "Cleaning up existing containers..."
    podman-compose down -v 2>/dev/null || true
    print_info "✓ Cleanup completed"
}

# Function to build images
build_images() {
    print_info "Building container images..."
    podman-compose build --no-cache
    print_info "✓ Images built successfully"
}

# Function to start services
start_services() {
    print_info "Starting services..."
    podman-compose up -d
    print_info "✓ Services started"
}

# Function to check service health
check_health() {
    print_info "Waiting for services to be healthy..."
    
    # Wait for PostgreSQL
    local max_attempts=30
    local attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if podman exec insurance-postgres pg_isready -U postgres -d insurance_rag >/dev/null 2>&1; then
            print_info "✓ PostgreSQL is ready"
            break
        fi
        attempt=$((attempt + 1))
        echo -n "."
        sleep 2
    done
    
    if [ $attempt -eq $max_attempts ]; then
        print_error "PostgreSQL failed to start"
        return 1
    fi
    
    # Wait for application
    attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if curl -sf http://localhost:8501/_stcore/health >/dev/null 2>&1; then
            print_info "✓ Application is ready"
            break
        fi
        attempt=$((attempt + 1))
        echo -n "."
        sleep 2
    done
    
    if [ $attempt -eq $max_attempts ]; then
        print_error "Application failed to start"
        return 1
    fi
    
    return 0
}

# Function to display service info
show_info() {
    echo ""
    print_info "============================================"
    print_info "  Insurance RAG Application - Running!  "
    print_info "============================================"
    echo ""
    print_info "📊 Application URL: http://localhost:8501"
    print_info "🗄️  PostgreSQL: localhost:5432"
    echo ""
    print_info "Useful commands:"
    echo "  • View logs:        podman-compose logs -f"
    echo "  • View app logs:    podman-compose logs -f rag-app"
    echo "  • View DB logs:     podman-compose logs -f postgres"
    echo "  • Stop services:    podman-compose down"
    echo "  • Restart services: podman-compose restart"
    echo "  • Access DB:        podman exec -it insurance-postgres psql -U postgres -d insurance_rag"
    echo ""
    print_info "Press Ctrl+C to view logs (containers will keep running)"
    print_info "============================================"
    echo ""
}

# Main deployment flow
main() {
    print_info "Starting Podman deployment..."
    
    # Cleanup old containers
    cleanup
    
    # Build images
    build_images
    
    # Start services
    start_services
    
    # Check health
    if check_health; then
        show_info
        
        # Show logs
        podman-compose logs -f
    else
        print_error "Deployment failed. Check logs with: podman-compose logs"
        podman-compose logs
        exit 1
    fi
}

# Parse command line arguments
case "${1:-deploy}" in
    deploy)
        main
        ;;
    
    start)
        print_info "Starting existing services..."
        podman-compose start
        check_health && show_info
        ;;
    
    stop)
        print_info "Stopping services..."
        podman-compose stop
        print_info "✓ Services stopped"
        ;;
    
    restart)
        print_info "Restarting services..."
        podman-compose restart
        check_health && show_info
        ;;
    
    clean)
        print_info "Cleaning up all containers and volumes..."
        podman-compose down -v
        rm -rf data/postgres/* data/app/* logs/*
        print_info "✓ Cleanup completed"
        ;;
    
    logs)
        podman-compose logs -f
        ;;
    
    status)
        print_info "Service status:"
        podman-compose ps
        ;;
    
    rebuild)
        print_info "Rebuilding containers..."
        cleanup
        build_images
        start_services
        check_health && show_info
        ;;
    
    *)
        echo "Usage: $0 {deploy|start|stop|restart|clean|logs|status|rebuild}"
        echo ""
        echo "Commands:"
        echo "  deploy   - Full deployment (cleanup, build, start)"
        echo "  start    - Start existing containers"
        echo "  stop     - Stop running containers"
        echo "  restart  - Restart containers"
        echo "  clean    - Remove all containers and data"
        echo "  logs     - Show container logs"
        echo "  status   - Show container status"
        echo "  rebuild  - Rebuild and redeploy"
        exit 1
        ;;
esac
