#!/bin/bash

# Fauxdan Admin Services Startup Script
echo "🚀 Starting Fauxdan Admin Services..."

# Check if .env.dev exists
if [ ! -f ".env.dev" ]; then
    echo "❌ Error: .env.dev file not found!"
    echo "Please create .env.dev file with your environment variables first."
    exit 1
fi

# Start admin services
echo "📦 Starting admin services..."
docker compose --env-file .env.dev -f docker-compose.dev.yml up -d caddy-admin backend-admin

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service status
echo "🔍 Checking service status..."
docker compose --env-file .env.dev -f docker-compose.dev.yml ps caddy-admin backend-admin

echo ""
echo "✅ Admin services started!"
echo ""
echo "🌐 Access your admin panel at:"
echo "   - Main Admin Panel: https://localhost:8443"
echo "   - Django Admin: https://localhost:8443/admin"
echo "   - Grafana: https://localhost:8443/grafana"
echo "   - Prometheus: https://localhost:8443/prometheus"
echo ""
echo "🔧 To stop admin services:"
echo "   docker compose --env-file .env.dev -f docker-compose.dev.yml stop caddy-admin backend-admin"
echo ""
echo "📊 To view logs:"
echo "   docker compose --env-file .env.dev -f docker-compose.dev.yml logs -f caddy-admin backend-admin"
