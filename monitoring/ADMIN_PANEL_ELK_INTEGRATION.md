# ELK Stack Integration with Admin Panel

This document describes how the ELK (Elasticsearch, Logstash, Kibana) stack has been integrated with the Fauxdan admin panel for centralized access and management.

## Overview

The ELK stack services are now accessible through the admin panel at `https://localhost:8443`, providing a unified interface for monitoring, logging, and administration.

## Admin Panel Services

### 1. Django Admin
- **URL**: `https://localhost:8443/admin`
- **Purpose**: Application data management and user administration
- **Access**: Direct Django admin interface

### 2. Grafana Dashboards
- **URL**: `https://localhost:8443/grafana`
- **Purpose**: Metrics visualization and monitoring dashboards
- **Features**: System metrics, application metrics, custom dashboards

### 3. Prometheus
- **URL**: `https://localhost:8443/prometheus`
- **Purpose**: Raw metrics data and alerting configuration
- **Features**: Query interface, alert rules, target monitoring

### 4. Kibana Logs
- **URL**: `https://localhost:8443/kibana`
- **Purpose**: Log exploration and analysis
- **Features**: Log search, filtering, visualization, dashboards

### 5. Elasticsearch
- **URL**: `https://localhost:8443/elasticsearch`
- **Purpose**: Direct access to Elasticsearch API
- **Features**: Index management, query interface, cluster health

### 6. Logstash
- **URL**: `https://localhost:8443/logstash`
- **Purpose**: Log processing pipeline monitoring
- **Features**: Pipeline status, configuration, performance metrics

## Configuration Changes

### 1. Caddy Admin Configuration
Updated `caddy/Caddyfile.admin.dev` to include ELK service routing:

```caddy
# Route Elasticsearch to the elasticsearch service
handle /elasticsearch {
    uri strip_prefix /elasticsearch
    reverse_proxy elasticsearch:9200
}

# Route Kibana to the kibana service
handle /kibana {
    reverse_proxy kibana:5601
}

# Route Logstash monitoring to the logstash service
handle /logstash {
    uri strip_prefix /logstash
    reverse_proxy logstash:9600
}
```

### 2. Kibana Configuration
Updated `monitoring/kibana/kibana.yml` for reverse proxy support:

```yaml
# Configure Kibana to work behind reverse proxy
server.basePath: "/kibana"
server.rewriteBasePath: true
```

### 3. Docker Compose Updates
- Removed direct port mapping for Kibana (now accessed through admin panel)
- All ELK services use internal networking only
- Services are exposed through Caddy reverse proxy

### 4. Admin Panel Interface
Updated `monitoring/admin/index.html` with:
- New service cards for ELK components
- Enhanced status checking for all services
- Improved visual indicators for service health

## Access Methods

### Primary Access (Recommended)
1. **Admin Panel**: `https://localhost:8443`
2. **Service Selection**: Click on desired service card
3. **Direct Navigation**: Use service-specific URLs

### Direct Service Access
- **Kibana**: `https://localhost:8443/kibana`
- **Elasticsearch**: `https://localhost:8443/elasticsearch`
- **Logstash**: `https://localhost:8443/logstash`

## Security Features

### HTTPS Encryption
- All services accessed through HTTPS
- Self-signed certificates for development
- Secure communication between services

### Access Control
- Services accessible only through admin panel
- No direct external port exposure
- Centralized authentication point

### Network Isolation
- ELK services on internal Docker network
- Reverse proxy provides controlled access
- No direct internet exposure

## Service Health Monitoring

### Automatic Status Checking
The admin panel automatically checks service health:

```javascript
const services = [
    { name: 'Django Admin', url: '/admin' },
    { name: 'Grafana', url: '/grafana' },
    { name: 'Prometheus', url: '/prometheus' },
    { name: 'Kibana', url: '/kibana' },
    { name: 'Elasticsearch', url: '/elasticsearch/_cluster/health' },
    { name: 'Logstash', url: '/logstash/_node/stats' }
];
```

### Visual Indicators
- **Green**: All services operational
- **Red**: Some services down
- **Real-time**: Status updates on page load

## Log Collection Workflow

### 1. Log Generation
- **Django**: Structured JSON logs with request context
- **Caddy**: JSON access logs
- **Docker**: Container stdout/stderr
- **System**: Host system logs

### 2. Log Processing
- **Logstash**: Collects and processes logs
- **Parsing**: JSON parsing and field extraction
- **Enrichment**: Adds metadata and tags
- **Routing**: Sends to Elasticsearch

### 3. Log Storage
- **Elasticsearch**: Stores processed logs
- **Indexing**: Daily indices with retention
- **Search**: Full-text search capabilities
- **Analytics**: Aggregation and analysis

### 4. Log Visualization
- **Kibana**: Web-based log exploration
- **Dashboards**: Pre-configured visualizations
- **Discover**: Interactive log browsing
- **Alerts**: Real-time monitoring

## Usage Examples

### Viewing Application Logs
1. Access admin panel: `https://localhost:8443`
2. Click "Open Kibana"
3. Navigate to "Discover"
4. Select "fauxdan-logs-*" index pattern
5. Filter and search logs

### Monitoring System Health
1. Access admin panel: `https://localhost:8443`
2. Click "Open Grafana"
3. View system overview dashboard
4. Check metrics and alerts

### Querying Elasticsearch
1. Access admin panel: `https://localhost:8443`
2. Click "Access Elasticsearch"
3. Use REST API for queries
4. Manage indices and mappings

### Checking Log Processing
1. Access admin panel: `https://localhost:8443`
2. Click "View Logstash"
3. Monitor pipeline status
4. Check processing metrics

## Troubleshooting

### Service Not Accessible
1. Check admin panel status indicator
2. Verify service is running: `docker-compose ps`
3. Check service logs: `docker-compose logs <service>`
4. Restart service if needed

### Kibana Not Loading
1. Check Elasticsearch connectivity
2. Verify Kibana configuration
3. Check reverse proxy routing
4. Review Kibana logs

### Logs Not Appearing
1. Check Logstash pipeline status
2. Verify log sources are active
3. Check Elasticsearch indices
4. Review Logstash configuration

## Benefits

### Centralized Access
- Single entry point for all services
- Consistent interface and navigation
- Unified authentication and security

### Enhanced Security
- No direct port exposure
- HTTPS encryption for all services
- Centralized access control

### Improved User Experience
- Intuitive service selection
- Real-time status monitoring
- Consistent branding and interface

### Simplified Management
- Single configuration point
- Centralized logging and monitoring
- Unified troubleshooting interface

## Future Enhancements

### Authentication Integration
- Single sign-on for all services
- Role-based access control
- User session management

### Advanced Monitoring
- Service dependency mapping
- Performance metrics integration
- Automated alerting

### Custom Dashboards
- Service-specific dashboards
- Cross-service correlation
- Business metrics integration

## Maintenance

### Regular Tasks
- Monitor service health through admin panel
- Review log volumes and patterns
- Update service configurations as needed
- Backup important configurations

### Updates
- Keep ELK stack versions current
- Update admin panel interface
- Enhance security configurations
- Add new service integrations

This integration provides a comprehensive, secure, and user-friendly interface for managing all aspects of the Fauxdan application stack through a single admin panel.
