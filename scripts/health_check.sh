#!/bin/bash

set -e

echo "🔍 Running LLM Platform Health Check..."

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
API_URL="http://localhost:8000"
TIMEOUT=10

# Functions
check_service() {
    local name=$1
    local url=$2
    local expected_status=${3:-200}
    
    echo -n "Checking $name... "
    
    if curl -s -f --max-time $TIMEOUT "$url" > /dev/null; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${RED}✗${NC}"
        return 1
    fi
}

check_container() {
    local name=$1
    
    echo -n "Checking container $name... "
    
    if docker-compose ps | grep "$name" | grep -q "Up"; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${RED}✗${NC}"
        return 1
    fi
}

check_disk_space() {
    echo -n "Checking disk space... "
    
    FREE_SPACE=$(df -BG . | tail -1 | awk '{print $4}' | sed 's/G//')
    if [ "$FREE_SPACE" -lt 10 ]; then
        echo -e "${RED}✗ (Low: ${FREE_SPACE}G)${NC}"
        return 1
    else
        echo -e "${GREEN}✓ (${FREE_SPACE}G free)${NC}"
        return 0
    fi
}

check_memory() {
    echo -n "Checking memory... "
    
    FREE_MEM=$(free -m | awk 'NR==2{print $4}')
    if [ "$FREE_MEM" -lt 500 ]; then
        echo -e "${YELLOW}⚠ (Low: ${FREE_MEM}MB)${NC}"
        return 1
    else
        echo -e "${GREEN}✓ (${FREE_MEM}MB free)${NC}"
        return 0
    fi
}

# Main checks
echo ""
echo "📊 System Health:"
check_disk_space
check_memory

echo ""
echo "🐳 Container Health:"
check_container "api"
check_container "postgres"
check_container "redis"
check_container "ollama"
check_container "prometheus"
check_container "grafana"

echo ""
echo "🌐 Service Health:"
check_service "API" "$API_URL/health"
check_service "API Docs" "$API_URL/docs"
check_service "Grafana" "http://localhost:3000"
check_service "Prometheus" "http://localhost:9090"
check_service "MLflow" "http://localhost:5000"

echo ""
echo "🔍 Detailed Checks:"

# Check API response
echo -n "API response time... "
API_TIME=$(curl -s -w "%{time_total}" -o /dev/null "$API_URL/health")
echo -e "${GREEN}${API_TIME}s${NC}"

# Check database
echo -n "Database connection... "
if docker-compose exec postgres pg_isready -U llm_user > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
fi

# Check Redis
echo -n "Redis connection... "
if docker-compose exec redis redis-cli ping | grep -q "PONG"; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
fi

# Check models
echo -n "Ollama models... "
MODEL_COUNT=$(docker-compose exec ollama ollama list | wc -l)
if [ "$MODEL_COUNT" -gt 1 ]; then
    echo -e "${GREEN}✓ ($((MODEL_COUNT-1)) models)${NC}"
else
    echo -e "${YELLOW}⚠ (No models found)${NC}"
fi

echo ""
echo "📈 Summary:"
echo "Run 'docker-compose logs' for detailed logs"
echo "Run './scripts/backup.sh' to create backup"
echo "Visit http://localhost:8000/docs for API documentation"
