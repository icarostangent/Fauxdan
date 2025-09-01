#!/bin/bash

# Test PostgreSQL Monitoring Script
# This script verifies that PostgreSQL monitoring is working correctly

set -e

echo "🧪 Testing PostgreSQL monitoring setup..."

# Function to test endpoint
test_endpoint() {
    local url=$1
    local name=$2
    local expected_content=$3
    
    echo "Testing $name at $url..."
    
    if curl -s "$url" | grep -q "$expected_content"; then
        echo "✅ $name is working correctly"
        return 0
    else
        echo "❌ $name is not working correctly"
        return 1
    fi
}

# Function to test Prometheus query
test_prometheus_query() {
    local query=$1
    local description=$2
    
    echo "Testing Prometheus query: $description"
    
    if curl -s "http://localhost:9090/api/v1/query?query=$query" | grep -q '"result":\[.*\]'; then
        echo "✅ $description: Metric data available"
        return 0
    else
        echo "❌ $description: No data returned"
        return 1
    fi
}

# Check if services are running
echo "🔍 Checking if monitoring services are running..."
if ! docker compose --env-file .env.dev -f docker-compose.dev.yml ps | grep -q "postgres-exporter.*Up"; then
    echo "❌ PostgreSQL exporter is not running. Please start it first:"
    echo "   ./setup-postgres-monitoring.sh"
    exit 1
fi

# Test PostgreSQL Exporter
echo ""
echo "📊 Testing PostgreSQL Exporter..."
if test_endpoint "http://localhost:9187/metrics" "PostgreSQL Exporter" "pg_"; then
    echo "✅ PostgreSQL Exporter is accessible and providing metrics"
else
    echo "❌ PostgreSQL Exporter is not accessible or not providing metrics"
fi

# Test Prometheus
echo ""
echo "📈 Testing Prometheus..."
if test_endpoint "http://localhost:9090/api/v1/targets" "Prometheus" "postgres-exporter"; then
    echo "✅ Prometheus is accessible and has postgres-exporter target"
else
    echo "❌ Prometheus is not accessible or missing postgres-exporter target"
fi

# Test Grafana
echo ""
echo "📊 Testing Grafana..."
if test_endpoint "http://localhost:3001" "Grafana" "login"; then
    echo "✅ Grafana is accessible"
else
    echo "❌ Grafana is not accessible"
fi

# Test specific PostgreSQL metrics
echo ""
echo "🔍 Testing PostgreSQL metrics collection..."

# Test basic PostgreSQL status
if test_prometheus_query "pg_up" "PostgreSQL status"; then
    echo "✅ PostgreSQL status metric is working"
else
    echo "❌ PostgreSQL status metric is not working"
fi

# Test connection count
if test_prometheus_query "pg_stat_database_numbackends" "PostgreSQL connection count"; then
    echo "✅ PostgreSQL connection count metric is working"
else
    echo "❌ PostgreSQL connection count metric is not working"
fi

# Test database size
if test_prometheus_query "pg_database_size_bytes" "PostgreSQL database size"; then
    echo "✅ PostgreSQL database size metric is working"
else
    echo "❌ PostgreSQL database size metric is not working"
fi

# Test transaction metrics
if test_prometheus_query "rate(pg_stat_database_xact_commit[5m])" "PostgreSQL transaction rate"; then
    echo "✅ PostgreSQL transaction rate metric is working"
else
    echo "❌ PostgreSQL transaction rate metric is not working"
fi

echo ""
echo "🎯 PostgreSQL Monitoring Test Summary:"
echo "======================================"

# Check if all critical metrics are working
echo "📊 To view your PostgreSQL metrics:"
echo "   1. Open Grafana: http://localhost:3001"
echo "   2. Login with admin/admin123"
echo "   3. Go to Dashboards"
echo "   4. Look for 'PostgreSQL Database Metrics'"
echo ""
echo "🔍 To check raw metrics:"
echo "   - PostgreSQL Exporter: http://localhost:9187/metrics"
echo "   - Prometheus: http://localhost:9090"
echo ""
echo "📈 To check specific metrics in Prometheus:"
echo "   - PostgreSQL status: pg_up"
echo "   - Active connections: pg_stat_database_numbackends"
echo "   - Database size: pg_database_size_bytes"
echo "   - Transaction rate: rate(pg_stat_database_xact_commit[5m])"
