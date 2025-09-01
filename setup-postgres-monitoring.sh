#!/bin/bash

# PostgreSQL Monitoring Setup Script for Fauxdan
# This script sets up the environment and starts PostgreSQL monitoring

set -e

echo "🚀 Setting up PostgreSQL monitoring for Fauxdan..."

# Check if .env.dev exists, if not create it
if [ ! -f .env.dev ]; then
    echo "📝 Creating .env.dev file..."
    cat > .env.dev << 'EOF'
SSL_RENEWAL_INTERVAL=0 12 * * *
DOMAIN_NAME=localhost
COMPOSE_PROJECT_NAME=fauxdan
LETSENCRYPT_EMAIL=icarostangent@gmail.com

POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres123
POSTGRES_HOST=db

VUE_APP_API_URL=http://localhost

DJANGO_SECRET_KEY=dev-secret-key-change-in-production
DJANGO_DB_NAME=fauxdan
DJANGO_DB_USER=fauxdan
DJANGO_DB_PASSWORD=fauxdan123
DJANGO_DB_HOST=db
DJANGO_DB_PORT=5432

POSTGRES_EXTRA_OPTS=-Z1 --schema=public --blobs
SCHEDULE=@daily
BACKUP_ON_START=TRUE
BACKUP_KEEP_DAYS=7
BACKUP_KEEP_WEEKS=4
BACKUP_KEEP_MONTHS=6
HEALTHCHECK_PORT=8080
EOF
    echo "✅ .env.dev file created"
else
    echo "✅ .env.dev file already exists"
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed. Please install it and try again."
    exit 1
fi

echo "🐳 Starting PostgreSQL monitoring services..."

# Start the monitoring services with .env.dev
docker-compose --env-file .env.dev -f docker-compose.dev.yml up -d prometheus grafana node-exporter redis-exporter postgres-exporter

echo "⏳ Waiting for services to start..."
sleep 10

# Check service status
echo "📊 Checking service status..."
docker-compose --env-file .env.dev -f docker-compose.dev.yml ps prometheus grafana node-exporter redis-exporter postgres-exporter

echo ""
echo "🎉 PostgreSQL monitoring setup complete!"
echo ""
echo "📈 Access your monitoring dashboards:"
echo "   - Prometheus: http://localhost:9090"
echo "   - Grafana: http://localhost:3001 (admin/admin123)"
echo "   - PostgreSQL Exporter: http://localhost:9187/metrics"
echo ""
echo "🔍 To view PostgreSQL metrics in Grafana:"
echo "   1. Go to http://localhost:3001"
echo "   2. Login with admin/admin123"
echo "   3. Navigate to Dashboards"
echo "   4. Look for 'PostgreSQL Database Metrics'"
echo ""
echo "🛑 To stop monitoring services:"
echo "   docker-compose --env-file .env.dev -f docker-compose.dev.yml stop prometheus grafana node-exporter redis-exporter postgres-exporter"
echo ""
echo "🔄 To restart services:"
echo "   docker-compose --env-file .env.dev -f docker-compose.dev.yml restart prometheus grafana node-exporter redis-exporter postgres-exporter"
