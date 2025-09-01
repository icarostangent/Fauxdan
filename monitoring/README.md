# Fauxdan Monitoring & Metrics

This directory contains the monitoring and metrics infrastructure for the Fauxdan project using Prometheus and Grafana.

## Architecture

The monitoring stack consists of:

- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards
- **Node Exporter**: System metrics (CPU, memory, disk, network)
- **Redis Exporter**: Redis performance metrics
- **PostgreSQL Exporter**: Database performance metrics
- **Custom Django Metrics**: Application-specific business metrics

## Services

### Prometheus
- **Port**: 9090
- **URL**: http://localhost:9090
- **Purpose**: Central metrics collection, storage, and alerting
- **Configuration**: `prometheus/prometheus.yml`
- **Alert Rules**: `prometheus/rules/alerts.yml`

### Grafana
- **Port**: 3001 (mapped from container port 3000)
- **URL**: http://localhost:3001
- **Default Credentials**: admin/admin123
- **Purpose**: Metrics visualization and dashboards
- **Configuration**: `grafana/provisioning/`

### Node Exporter
- **Port**: 9100
- **Purpose**: Host system metrics collection
- **Metrics**: CPU, memory, disk, network, process information

### Redis Exporter
- **Port**: 9121
- **Purpose**: Redis performance and connection metrics
- **Metrics**: Connected clients, memory usage, command statistics

### PostgreSQL Exporter
- **Port**: 9187
- **Purpose**: Database performance metrics
- **Metrics**: Connection pools, query performance, table statistics

## Quick Start

### 1. Start the Monitoring Stack

```bash
# Start all services including monitoring
docker-compose -f docker-compose.dev.yml up -d

# Or start just the monitoring services
docker-compose -f docker-compose.dev.yml up -d prometheus grafana node-exporter redis-exporter postgres-exporter
```

### 2. Access the Services

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001 (admin/admin123)
- **Node Exporter**: http://localhost:9100/metrics
- **Redis Exporter**: http://localhost:9121/metrics
- **PostgreSQL Exporter**: http://localhost:9187/metrics

### 3. Import Dashboards

Grafana will automatically load the pre-configured dashboards:
- **System Overview**: General system health and performance
- **Django Metrics**: Application-specific metrics (once implemented)

## Configuration

### Prometheus Configuration

The main configuration file is `prometheus/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
  
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
  
  # ... other targets
```

### Alert Rules

Alert rules are defined in `prometheus/rules/alerts.yml`:

- **ServiceDown**: Critical alerts for service unavailability
- **HighCPUUsage**: Warning alerts for high CPU usage (>80%)
- **HighMemoryUsage**: Warning alerts for high memory usage (>85%)
- **HighDiskUsage**: Warning alerts for high disk usage (>85%)
- **DatabaseIssues**: Critical alerts for database connectivity problems

### Grafana Configuration

#### Data Sources
- **Prometheus**: Automatically configured to connect to Prometheus
- **Configuration**: `grafana/provisioning/datasources/prometheus.yml`

#### Dashboards
- **Auto-provisioning**: Dashboards are automatically loaded from `grafana/dashboards/`
- **Configuration**: `grafana/provisioning/dashboards/dashboards.yml`

## Dashboards

### System Overview Dashboard

**Purpose**: General system health and performance monitoring

**Panels**:
- CPU Usage (percentage)
- Memory Usage (percentage)
- Disk Usage (percentage)
- Network Receive (bytes/sec)
- Service Status (up/down indicators)
- Redis Connected Clients

**Refresh Rate**: 5 seconds
**Time Range**: Last hour (configurable)

### Django Metrics Dashboard

**Purpose**: Application-specific business metrics

**Panels**:
- Request Rate (requests per second)
- 95th Percentile Response Time
- Error Rate (percentage)
- Total Requests by Status
- Total Visitors
- Total Page Views

**Refresh Rate**: 10 seconds
**Time Range**: Last hour (configurable)

## Metrics

### System Metrics (Node Exporter)

- **CPU**: Usage percentage, load average, per-core statistics
- **Memory**: Total, available, used, cached, buffered
- **Disk**: Usage percentage, I/O statistics, per-filesystem metrics
- **Network**: Bytes sent/received, packets, errors, drops
- **Process**: Running processes, system uptime

### Application Metrics (Django)

*Note: These metrics will be available once the Django metrics endpoint is implemented*

- **HTTP Requests**: Total count, rate, status codes
- **Response Times**: Duration histograms, percentiles
- **Error Rates**: 5xx errors, exception counts
- **Business Metrics**: Visitors, page views, user interactions

### Database Metrics (PostgreSQL Exporter)

- **Connections**: Active, idle, total connections
- **Query Performance**: Query times, slow queries
- **Table Statistics**: Row counts, index usage
- **Locks**: Active locks, deadlocks

### Cache Metrics (Redis Exporter)

- **Connections**: Connected clients, rejected connections
- **Memory**: Used memory, peak memory
- **Commands**: Command statistics, hit rates
- **Keys**: Total keys, expired keys

## Alerting

### Alert Severity Levels

- **Critical**: Service down, database connectivity issues
- **Warning**: High resource usage, slow response times
- **Info**: Configuration changes, deployments

### Alert Notifications

Currently configured for local development. For production, consider:
- **Slack/Teams**: Real-time notifications
- **Email**: Daily summaries
- **PagerDuty**: Escalation for critical incidents

## Development

### Adding New Metrics

1. **Define Metrics**: Create Prometheus metrics in your application
2. **Update Configuration**: Add new targets to `prometheus.yml`
3. **Create Dashboards**: Build Grafana dashboards for new metrics
4. **Set Alerts**: Define alert rules for critical thresholds

### Custom Dashboards

1. **Create JSON**: Export dashboard from Grafana or create manually
2. **Place in Directory**: Put in `grafana/dashboards/`
3. **Auto-load**: Dashboard will be automatically loaded on restart

### Testing Metrics

```bash
# Check if metrics are being collected
curl http://localhost:9090/api/v1/targets

# View specific metrics
curl http://localhost:9100/metrics | grep cpu

# Test Prometheus queries
curl "http://localhost:9090/api/v1/query?query=up"
```

## Troubleshooting

### Common Issues

#### Prometheus Not Scraping Targets

1. **Check Target Status**: http://localhost:9090/targets
2. **Verify Network**: Ensure containers can communicate
3. **Check Configuration**: Validate `prometheus.yml` syntax
4. **View Logs**: `docker-compose logs prometheus`

#### Grafana Can't Connect to Prometheus

1. **Check Data Source**: Verify Prometheus URL in Grafana
2. **Network Connectivity**: Ensure containers are on same network
3. **Service Health**: Verify Prometheus is running and healthy

#### Metrics Not Appearing

1. **Check Exporter Status**: Verify exporters are running
2. **Validate Metrics Endpoint**: Test `/metrics` endpoints directly
3. **Check Prometheus Targets**: Ensure targets are up and being scraped
4. **View Prometheus Logs**: Check for scraping errors

### Debug Commands

```bash
# Check service status
docker-compose -f docker-compose.dev.yml ps

# View service logs
docker-compose -f docker-compose.dev.yml logs prometheus
docker-compose -f docker-compose.dev.yml logs grafana

# Check network connectivity
docker exec fauxdan-prometheus-dev wget -qO- http://node-exporter:9100/metrics

# Restart monitoring services
docker-compose -f docker-compose.dev.yml restart prometheus grafana
```

## Production Considerations

### Security

- **Authentication**: Enable Grafana authentication
- **Network Security**: Restrict access to monitoring ports
- **TLS**: Use HTTPS for all monitoring endpoints
- **Access Control**: Implement role-based access control

### Performance

- **Storage**: Use persistent volumes for metrics data
- **Retention**: Configure appropriate data retention policies
- **Scraping**: Adjust scrape intervals based on metrics volume
- **Caching**: Implement metrics caching for frequently accessed data

### Scaling

- **Federation**: Use Prometheus federation for multiple instances
- **Long-term Storage**: Integrate with object storage (S3, GCS)
- **Load Balancing**: Distribute monitoring load across instances
- **High Availability**: Run multiple Prometheus instances

## Next Steps

1. **Implement Django Metrics**: Add Prometheus metrics to Django backend
2. **Frontend Metrics**: Add client-side performance metrics
3. **Custom Dashboards**: Create business-specific dashboards
4. **Alerting**: Configure production alert notifications
5. **Integration**: Connect with existing analytics system

## Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Node Exporter](https://github.com/prometheus/node_exporter)
- [Redis Exporter](https://github.com/oliver006/redis_exporter)
- [PostgreSQL Exporter](https://github.com/prometheus-community/postgres_exporter)
