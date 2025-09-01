# PostgreSQL Monitoring Setup for Fauxdan

This document explains how to set up and use PostgreSQL monitoring in the Fauxdan project using Prometheus, Grafana, and the PostgreSQL Exporter.

## 🚀 Quick Start

### 1. Setup Environment and Start Monitoring

```bash
# Make the setup script executable and run it
chmod +x setup-postgres-monitoring.sh
./setup-postgres-monitoring.sh
```

This script will:
- Create a `.env.dev` file with the necessary environment variables
- Start all monitoring services (Prometheus, Grafana, Node Exporter, Redis Exporter, PostgreSQL Exporter)
- Verify that services are running correctly

### 2. Test the Setup

```bash
# Test that PostgreSQL monitoring is working
./test-postgres-monitoring.sh
```

## 📊 What's Included

### Monitoring Stack
- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards
- **PostgreSQL Exporter**: Database metrics collection
- **Node Exporter**: System metrics
- **Redis Exporter**: Redis metrics

### PostgreSQL Metrics Collected
- **Connection Metrics**: Active connections, connection utilization
- **Performance Metrics**: Transaction rates, DML operations, query performance
- **Resource Metrics**: Database size, I/O performance, block read/write times
- **Health Metrics**: Database status, deadlocks, replication conflicts

## 🔧 Manual Setup

If you prefer to set up manually:

### 1. Create Environment File

Create a `.env.dev` file in the project root:

```bash
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
```

### 2. Start Monitoring Services

```bash
# Start only the monitoring services
docker-compose --env-file .env.dev -f docker-compose.dev.yml up -d prometheus grafana node-exporter redis-exporter postgres-exporter

# Or start all services including the database
docker-compose --env-file .env.dev -f docker-compose.dev.yml up -d
```

### 3. Verify Services

```bash
# Check service status
docker-compose --env-file .env.dev -f docker-compose.dev.yml ps

# Check logs for any errors
docker-compose --env-file .env.dev -f docker-compose.dev.yml logs postgres-exporter
```

## 📈 Accessing Monitoring

### URLs
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001 (admin/admin123)
- **PostgreSQL Exporter**: http://localhost:9187/metrics

### Grafana Dashboard
1. Login to Grafana with `admin/admin123`
2. Navigate to Dashboards
3. Look for "PostgreSQL Database Metrics" dashboard
4. The dashboard includes:
   - Active connections
   - Transaction rates
   - DML operations
   - Query performance
   - Database size
   - Deadlocks and conflicts
   - I/O performance

## 🔍 Key Metrics

### Connection Metrics
- `pg_stat_database_numbackends`: Number of active connections
- `postgresql:connections_utilization_percent`: Connection utilization percentage

### Performance Metrics
- `postgresql:transactions_per_second`: Transaction rate (commits + rollbacks)
- `postgresql:dml_operations_per_second`: DML operations rate (inserts + updates + deletes)
- `postgresql:tuples_per_second`: Query performance (tuples fetched + returned)

### Resource Metrics
- `postgresql:database_size_gb`: Database size in GB
- `postgresql:io_time_seconds`: Total I/O time in seconds

### Health Metrics
- `pg_up`: Database availability (1 = up, 0 = down)
- `pg_stat_database_deadlocks`: Number of deadlocks
- `pg_stat_database_conflicts`: Replication conflicts

## 🚨 Alerts

The monitoring system includes several alerts:

### Critical Alerts
- **PostgresDown**: Database is unreachable
- **ServiceDown**: Any monitoring service is down

### Warning Alerts
- **PostgresHighConnections**: More than 80 active connections
- **PostgresHighTransactionRate**: Transaction rate above 1000/sec
- **PostgresHighDeadlockRate**: Deadlock rate above 0.1/sec
- **PostgresHighReplicationConflicts**: Replication conflict rate above 0.1/sec
- **PostgresHighIOTime**: I/O time above 60 seconds

## 🛠️ Troubleshooting

### Common Issues

#### 1. PostgreSQL Exporter Can't Connect
```bash
# Check if database is running
docker-compose --env-file .env.dev -f docker-compose.dev.yml ps db

# Check database logs
docker-compose --env-file .env.dev -f docker-compose.dev.yml logs db

# Verify environment variables
docker-compose --env-file .env.dev -f docker-compose.dev.yml exec postgres-exporter env | grep DATA_SOURCE_NAME
```

#### 2. No Metrics in Prometheus
```bash
# Check if postgres-exporter is in Prometheus targets
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job == "postgres-exporter")'

# Check postgres-exporter logs
docker-compose --env-file .env.dev -f docker-compose.dev.yml logs postgres-exporter
```

#### 3. Grafana Can't Connect to Prometheus
```bash
# Check Prometheus is running
curl http://localhost:9090/api/v1/status/targets

# Check Grafana logs
docker-compose --env-file .env.dev -f docker-compose.dev.yml logs grafana
```

### Useful Commands

```bash
# Restart a specific service
docker-compose --env-file .env.dev -f docker-compose.dev.yml restart postgres-exporter

# View real-time logs
docker-compose --env-file .env.dev -f docker-compose.dev.yml logs -f postgres-exporter

# Check service health
docker-compose --env-file .env.dev -f docker-compose.dev.yml ps

# Stop all monitoring services
docker-compose --env-file .env.dev -f docker-compose.dev.yml stop prometheus grafana node-exporter redis-exporter postgres-exporter
```

## 📚 Advanced Configuration

### Custom Metrics
You can add custom PostgreSQL queries by modifying the postgres-exporter configuration. The current setup uses the default metrics collection.

### Recording Rules
Custom recording rules are defined in `monitoring/prometheus/rules/recording_rules.yml` to make common queries easier to use in dashboards and alerts.

### Alert Rules
Alert rules are defined in `monitoring/prometheus/rules/alerts.yml` with thresholds that can be adjusted based on your environment.

## 🔒 Security Notes

- Default Grafana credentials are `admin/admin123` - change these in production
- The `.env.dev` file contains development credentials - use proper secrets management in production
- All monitoring services are exposed on localhost only in development
- Consider using reverse proxy and authentication in production

## 📖 Additional Resources

- [PostgreSQL Exporter Documentation](https://github.com/prometheus-community/postgres_exporter)
- [Prometheus Query Language](https://prometheus.io/docs/prometheus/latest/querying/)
- [Grafana Dashboard Documentation](https://grafana.com/docs/grafana/latest/dashboards/)
- [PostgreSQL Statistics Views](https://www.postgresql.org/docs/current/monitoring-stats.html)
