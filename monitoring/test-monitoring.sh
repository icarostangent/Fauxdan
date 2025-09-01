#!/bin/bash

# Fauxdan Monitoring Stack Test Script
# This script tests the monitoring services to ensure they're working correctly

set -e

echo "🧪 Testing Fauxdan Monitoring Stack..."

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

# Function to test a service endpoint
test_endpoint() {
    local url=$1
    local description=$2
    local expected_content=$3
    
    print_status "Testing $description..."
    
    if curl -s --max-time 10 "$url" | grep -q "$expected_content"; then
        print_success "$description is working correctly"
        return 0
    else
        print_error "$description is not working correctly"
        return 1
    fi
}

# Function to test Prometheus query
test_prometheus_query() {
    local query=$1
    local description=$2
    
    print_status "Testing Prometheus query: $description..."
    
    local response
    response=$(curl -s --max-time 10 "http://localhost:9090/api/v1/query?query=$query")
    
    if echo "$response" | grep -q '"status":"success"'; then
        print_success "Prometheus query successful: $description"
        return 0
    else
        print_error "Prometheus query failed: $description"
        return 1
    fi
}

# Check if services are running
print_status "Checking if monitoring services are running..."

# Test Prometheus
if test_endpoint "http://localhost:9090" "Prometheus" "Prometheus"; then
    print_success "Prometheus is accessible"
else
    print_error "Prometheus is not accessible"
    exit 1
fi

# Test Grafana
if test_endpoint "http://localhost:3001" "Grafana" "Grafana"; then
    print_success "Grafana is accessible"
else
    print_error "Grafana is not accessible"
    exit 1
fi

# Test Node Exporter
if test_endpoint "http://localhost:9100/metrics" "Node Exporter" "node_"; then
    print_success "Node Exporter is accessible and providing metrics"
else
    print_error "Node Exporter is not accessible or not providing metrics"
    exit 1
fi

# Test Redis Exporter
if test_endpoint "http://localhost:9121/metrics" "Redis Exporter" "redis_"; then
    print_success "Redis Exporter is accessible and providing metrics"
else
    print_error "Redis Exporter is not accessible or not providing metrics"
    exit 1
fi

# Test PostgreSQL Exporter
if test_endpoint "http://localhost:9187/metrics" "PostgreSQL Exporter" "pg_"; then
    print_success "PostgreSQL Exporter is accessible and providing metrics"
else
    print_error "PostgreSQL Exporter is not accessible or not providing metrics"
    exit 1
fi

echo ""
print_status "Testing Prometheus functionality..."

# Test basic Prometheus queries
tests_passed=true

# Test up metric
if test_prometheus_query "up" "Service status check"; then
    print_success "Service status query working"
else
    print_error "Service status query failed"
    tests_passed=false
fi

# Test node metrics
if test_prometheus_query "node_cpu_seconds_total" "CPU metrics"; then
    print_success "CPU metrics query working"
else
    print_error "CPU metrics query failed"
    tests_passed=false
fi

# Test redis metrics
if test_prometheus_query "redis_up" "Redis status"; then
    print_success "Redis metrics query working"
else
    print_error "Redis metrics query failed"
    tests_passed=false
fi

# Test postgres metrics
if test_prometheus_query "pg_up" "PostgreSQL status"; then
    print_success "PostgreSQL metrics query working"
else
    print_error "PostgreSQL metrics query failed"
    tests_passed=false
fi

echo ""
print_status "Checking Prometheus targets..."

# Check if targets are being scraped
targets_response=$(curl -s --max-time 10 "http://localhost:9090/api/v1/targets")

if echo "$targets_response" | grep -q '"health":"up"'; then
    print_success "Prometheus is successfully scraping targets"
else
    print_warning "Some Prometheus targets may not be healthy"
fi

echo ""
print_status "Testing Grafana data source..."

# Test if Grafana can connect to Prometheus
grafana_response=$(curl -s --max-time 10 "http://localhost:3001/api/datasources")

if echo "$grafana_response" | grep -q "Prometheus"; then
    print_success "Grafana has Prometheus data source configured"
else
    print_warning "Grafana may not have Prometheus data source configured"
fi

echo ""
if [ "$tests_passed" = true ]; then
    print_success "All monitoring tests passed! 🎉"
    echo ""
    echo "📊 Your monitoring stack is working correctly:"
    echo "   ✅ Prometheus is collecting metrics"
    echo "   ✅ Grafana is accessible"
    echo "   ✅ Exporters are providing metrics"
    echo "   ✅ Basic queries are working"
    echo ""
    echo "🚀 Next steps:"
    echo "   1. Open Grafana: http://localhost:3001 (admin/admin123)"
    echo "   2. View the pre-configured dashboards"
    echo "   3. Explore metrics in Prometheus: http://localhost:9090"
    echo "   4. Implement Django metrics endpoint for application metrics"
else
    print_error "Some tests failed. Check the service logs:"
    echo "   docker-compose -f docker-compose.dev.yml logs [service-name]"
    exit 1
fi
