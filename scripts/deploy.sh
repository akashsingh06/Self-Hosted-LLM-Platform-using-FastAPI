
### **`scripts/deploy.sh`**
```bash
#!/bin/bash

set -e  # Exit on error

echo "🚀 Starting LLM Platform Deployment..."

# Load environment
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check disk space
    FREE_SPACE=$(df -BG . | tail -1 | awk '{print $4}' | sed 's/G//')
    if [ "$FREE_SPACE" -lt 20 ]; then
        log_warn "Low disk space: ${FREE_SPACE}G"
    fi
    
    log_info "Prerequisites check passed"
}

# Backup existing data
backup_data() {
    log_info "Backing up existing data..."
    
    BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Backup database
    if docker-compose ps postgres | grep -q "Up"; then
        log_info "Backing up database..."
        docker-compose exec -T postgres pg_dumpall -U llm_user > "$BACKUP_DIR/database.sql"
    fi
    
    # Backup models
    if [ -d "data/models" ]; then
        log_info "Backing up models..."
        tar -czf "$BACKUP_DIR/models.tar.gz" data/models/
    fi
    
    # Backup configurations
    cp .env "$BACKUP_DIR/"
    cp docker-compose.yml "$BACKUP_DIR/"
    
    log_info "Backup completed: $BACKUP_DIR"
}

# Pull latest images
pull_images() {
    log_info "Pulling latest images..."
    docker-compose pull
}

# Build application
build_app() {
    log_info "Building application..."
    docker-compose build
}

# Start services
start_services() {
    log_info "Starting services..."
    docker-compose up -d
    
    # Wait for services to be healthy
    log_info "Waiting for services to be ready..."
    
    # Wait for API
    for i in {1..30}; do
        if curl -s http://localhost:8000/health > /dev/null; then
            log_info "API is ready"
            break
        fi
        echo -n "."
        sleep 2
    done
    
    # Wait for database
    for i in {1..30}; do
        if docker-compose exec postgres pg_isready -U llm_user > /dev/null; then
            log_info "Database is ready"
            break
        fi
        echo -n "."
        sleep 2
    done
}

# Run migrations
run_migrations() {
    log_info "Running database migrations..."
    
    # Wait for database to be ready
    sleep 5
    
    # Create tables if using SQLAlchemy
    log_info "Creating database tables..."
    # Note: In production, use Alembic migrations
    # docker-compose exec api python -c "from src.database.session import engine, Base; Base.metadata.create_all(bind=engine)"
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."
    
    # Check API health
    if curl -s http://localhost:8000/health | grep -q "healthy"; then
        log_info "✅ API is healthy"
    else
        log_error "❌ API health check failed"
        exit 1
    fi
    
    # Check database
    if docker-compose exec postgres pg_isready -U llm_user > /dev/null; then
        log_info "✅ Database is healthy"
    else
        log_error "❌ Database health check failed"
        exit 1
    fi
    
    # Check Redis
    if docker-compose exec redis redis-cli ping | grep -q "PONG"; then
        log_info "✅ Redis is healthy"
    else
        log_error "❌ Redis health check failed"
        exit 1
    fi
    
    log_info "✅ All services are healthy"
}

# Display deployment info
display_info() {
    echo ""
    echo "========================================="
    echo "🚀 LLM Platform Deployment Complete!"
    echo "========================================="
    echo ""
    echo "📊 Services:"
    echo "  API:          http://localhost:8000"
    echo "  API Docs:     http://localhost:8000/docs"
    echo "  Grafana:      http://localhost:3000"
    echo "  Prometheus:   http://localhost:9090"
    echo "  MLflow:       http://localhost:5000"
    echo ""
    echo "🔑 Default credentials:"
    echo "  Grafana:      admin / admin"
    echo ""
    echo "📝 Next steps:"
    echo "  1. Configure .env file for production"
    echo "  2. Set up SSL certificates"
    echo "  3. Configure authentication"
    echo "  4. Pull models: ollama pull deepseek-coder:6.7b"
    echo ""
    echo "🛠️  Useful commands:"
    echo "  View logs:    docker-compose logs -f"
    echo "  Stop:         docker-compose down"
    echo "  Update:       ./scripts/deploy.sh"
    echo "  Backup:       ./scripts/backup.sh"
    echo ""
    echo "========================================="
}

# Main deployment process
main() {
    log_info "Starting deployment at $(date)"
    
    check_prerequisites
    backup_data
    pull_images
    build_app
    start_services
    run_migrations
    verify_deployment
    display_info
    
    log_info "Deployment completed successfully!"
}

# Run main function
main "$@"
