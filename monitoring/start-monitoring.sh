#!/bin/bash

# Fauxdan Monitoring Stack Startup Script
# This script starts the monitoring services and verifies they're running

set -e

echo "🚀 Starting Fauxdan Monitoring Stack..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    print_error "docker-compose is not installed or not in PATH"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "../docker-compose.dev.yml" ]; then
    print_error "Please run this script from the monitoring/ directory"
    exit 1
fi

# Start monitoring services
print_status "Starting monitoring services..."
cd ..
docker-compose -f docker-compose.dev.yml up -d prometheus grafana node-exporter redis-exporter postgres-exporter

# Wait for services to start
print_status "Waiting for services to start..."
sleep 10

# Check service status
print_status "Checking service status..."
docker-compose -f docker-compose.dev.yml ps prometheus grafana node-exporter redis-exporter postgres-exporter

# Function to check if a service is responding
check_service() {
    local service_name=$1
    local url=$2
    local description=$3
    
    print_status "Checking $description..."
    
    if curl -s --max-time 10 "$url" > /dev/null 2>&1; then
        print_success "$description is responding"
        return 0
    else
        print_error "$description is not responding"
        return 1
    fi
}

# Check each service
echo ""
print_status "Verifying service health..."

services_healthy=true

# Check Prometheus
if check_service "prometheus" "http://localhost:9090" "Prometheus"; then
    print_success "Prometheus is healthy"
else
    print_error "Prometheus is not healthy"
    services_healthy=false
fi

# Check Grafana
if check_service "grafana" "http://localhost:3001" "Grafana"; then
    print_success "Grafana is healthy"
else
    print_error "Grafana is not healthy"
    services_healthy=false
fi

# Check Node Exporter
if check_service "node-exporter" "http://localhost:9100/metrics" "Node Exporter"; then
    print_success "Node Exporter is healthy"
else
    print_error "Node Exporter is not healthy"
    services_healthy=false
fi

# Check Redis Exporter
if check_service "redis-exporter" "http://localhost:9121/metrics" "Redis Exporter"; then
    print_success "Redis Exporter is healthy"
else
    print_error "Redis Exporter is not healthy"
    services_healthy=false
fi

# Check PostgreSQL Exporter
if check_service "postgres-exporter" "http://localhost:9187/metrics" "PostgreSQL Exporter"; then
    print_success "PostgreSQL Exporter is healthy"
else
    print_error "PostgreSQL Exporter is not healthy"
    services_healthy=false
fi

echo ""
if [ "$services_healthy" = true ]; then
    print_success "All monitoring services are running and healthy!"
    echo ""
    echo "📊 Access your monitoring stack:"
    echo "   Prometheus:     http://localhost:9090"
    echo "   Grafana:        http://localhost:3001 (admin/admin123)"
    echo "   Node Exporter:  http://localhost:9100/metrics"
    echo "   Redis Exporter: http://localhost:9121/metrics"
    echo "   Postgres Exporter: http://localhost:9187/metrics"
    echo ""
    echo "📈 Dashboards available:"
    echo "   - System Overview: General system health"
    echo "   - Django Metrics: Application metrics (once implemented)"
    echo ""
    print_success "Monitoring stack is ready!"
else
    print_error "Some services are not healthy. Check the logs:"
    echo "   docker-compose -f docker-compose.dev.yml logs [service-name]"
    exit 1
fi
