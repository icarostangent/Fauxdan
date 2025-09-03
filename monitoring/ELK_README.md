# ELK Stack Implementation for Fauxdan

This document describes the ELK (Elasticsearch, Logstash, Kibana) stack implementation for log collection, processing, and visualization in the Fauxdan development environment.

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Application   │    │    Logstash     │    │  Elasticsearch  │    │     Kibana      │
│     Logs        │───▶│   Processing    │───▶│    Storage      │───▶│  Visualization  │
│                 │    │                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Components

### 1. Elasticsearch
- **Purpose**: Log storage and search engine
- **Port**: 9200 (internal), 9300 (transport)
- **Configuration**: `monitoring/elasticsearch/elasticsearch.yml`
- **Features**:
  - Single-node cluster for development
  - Security disabled for easy setup
  - Optimized for log storage with daily indices

### 2. Logstash
- **Purpose**: Log processing and forwarding
- **Ports**: 5044 (Beats), 514 (Syslog)
- **Configuration**: `monitoring/logstash/logstash.conf`
- **Features**:
  - Docker container log collection
  - JSON log parsing
  - Structured log processing
  - Multiple input sources (Docker, files, syslog)

### 3. Kibana
- **Purpose**: Log visualization and analysis
- **Port**: 5601 (mapped to localhost:5601)
- **Configuration**: `monitoring/kibana/kibana.yml`
- **Features**:
  - Web-based log exploration
  - Dashboard creation
  - Real-time log monitoring
  - Index pattern management

## Log Sources

### 1. Django Application Logs
- **Format**: Structured JSON logs
- **Location**: Container stdout/stderr
- **Fields**:
  - `timestamp`: ISO 8601 timestamp
  - `level`: Log level (DEBUG, INFO, WARN, ERROR)
  - `message`: Log message
  - `request_id`: Unique request identifier
  - `method`: HTTP method
  - `path`: Request path
  - `status_code`: HTTP response code
  - `response_time`: Request duration
  - `user_id`: Authenticated user ID
  - `ip_address`: Client IP address

### 2. Caddy Web Server Logs
- **Format**: JSON access logs
- **Location**: Container stdout
- **Fields**:
  - `client_ip`: Client IP address
  - `method`: HTTP method
  - `request_path`: Requested path
  - `status_code`: HTTP status code
  - `response_size`: Response size in bytes
  - `user_agent`: Client user agent
  - `referer`: Referer header

### 3. Docker Container Logs
- **Format**: Container stdout/stderr
- **Location**: Docker daemon
- **Fields**:
  - `container.name`: Container name
  - `container.id`: Container ID
  - `message`: Log message
  - `timestamp`: Log timestamp

### 4. System Logs
- **Format**: Syslog format
- **Location**: Host system
- **Fields**:
  - Standard syslog fields
  - System-level events

## Quick Start

### 1. Start ELK Stack
```bash
# Start all ELK services
./monitoring/start-elk.sh

# Or start manually
docker-compose -f docker-compose.dev.yml up -d elasticsearch logstash kibana
```

### 2. Access Services
- **Admin Panel**: https://localhost:8443
- **Kibana**: https://localhost:8443/kibana
- **Elasticsearch**: https://localhost:8443/elasticsearch
- **Logstash**: https://localhost:8443/logstash
- **Grafana**: https://localhost:8443/grafana (with log integration)

### 3. Test Log Collection
```bash
# Run the test script
./monitoring/test-elk.sh
```

## Configuration Files

### Elasticsearch Configuration
```yaml
# monitoring/elasticsearch/elasticsearch.yml
cluster.name: "fauxdan-dev"
node.name: "fauxdan-node-1"
discovery.type: single-node
xpack.security.enabled: false
```

### Logstash Configuration
```ruby
# monitoring/logstash/logstash.conf
input {
  docker {
    host => "unix:///var/run/docker.sock"
    type => "docker"
  }
}

filter {
  # Parse and enrich logs
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "fauxdan-logs-%{+YYYY.MM.dd}"
  }
}
```

### Kibana Configuration
```yaml
# monitoring/kibana/kibana.yml
server.host: "0.0.0.0"
elasticsearch.hosts: ["http://elasticsearch:9200"]
xpack.security.enabled: false
```

## Log Processing Pipeline

### 1. Input Stage
- **Docker Logs**: Container stdout/stderr via Docker socket
- **File Logs**: Application log files
- **Syslog**: System logs via UDP/TCP

### 2. Filter Stage
- **JSON Parsing**: Parse structured JSON logs
- **Grok Patterns**: Extract fields from unstructured logs
- **Field Enrichment**: Add metadata (environment, project, etc.)
- **Tagging**: Add tags for categorization

### 3. Output Stage
- **Elasticsearch**: Store processed logs
- **Index Management**: Daily indices with retention
- **Template Application**: Apply field mappings

## Grafana Integration

### Data Source Configuration
```yaml
# monitoring/grafana/provisioning/datasources/elasticsearch.yml
datasources:
  - name: Elasticsearch
    type: elasticsearch
    url: http://elasticsearch:9200
    database: "fauxdan-logs-*"
```

### Dashboards
- **Application Logs Dashboard**: `monitoring/grafana/dashboards/application-logs.json`
  - Log volume over time
  - Log level distribution
  - Container log breakdown
  - Error rate monitoring
  - Recent logs viewer

## Log Analysis Examples

### 1. Find All Errors
```json
{
  "query": {
    "term": {
      "log_level": "ERROR"
    }
  }
}
```

### 2. Find Slow Requests
```json
{
  "query": {
    "range": {
      "response_time": {
        "gte": 1.0
      }
    }
  }
}
```

### 3. Find Requests by User
```json
{
  "query": {
    "term": {
      "user_id": "123"
    }
  }
}
```

### 4. Find Requests by IP
```json
{
  "query": {
    "term": {
      "ip_address": "192.168.1.100"
    }
  }
}
```

## Monitoring and Alerting

### Health Checks
- **Elasticsearch**: `curl -k https://localhost:8443/elasticsearch/_cluster/health`
- **Kibana**: `curl -k https://localhost:8443/kibana/api/status`
- **Logstash**: `curl -k https://localhost:8443/logstash/_node/stats`

### Key Metrics
- **Log Volume**: Number of logs per minute/hour
- **Error Rate**: Percentage of ERROR level logs
- **Response Time**: Average request duration
- **Container Health**: Log output from containers

### Alerting Rules
- **High Error Rate**: > 5% ERROR logs
- **No Logs**: No logs received in 5 minutes
- **High Log Volume**: > 1000 logs per minute
- **Slow Requests**: > 2 second response time

## Troubleshooting

### Common Issues

#### 1. Elasticsearch Not Starting
```bash
# Check memory limits
docker-compose -f docker-compose.dev.yml logs elasticsearch

# Check disk space
df -h

# Restart with more memory
docker-compose -f docker-compose.dev.yml restart elasticsearch
```

#### 2. Logstash Not Processing Logs
```bash
# Check Logstash logs
docker-compose -f docker-compose.dev.yml logs logstash

# Test configuration
docker-compose -f docker-compose.dev.yml exec logstash logstash --config.test_and_exit --config.reload.automatic

# Check Docker socket access
docker-compose -f docker-compose.dev.yml exec logstash ls -la /var/run/docker.sock
```

#### 3. Kibana Not Connecting to Elasticsearch
```bash
# Check Elasticsearch connectivity
curl http://localhost:9200/_cluster/health

# Check Kibana logs
docker-compose -f docker-compose.dev.yml logs kibana

# Restart Kibana
docker-compose -f docker-compose.dev.yml restart kibana
```

#### 4. No Logs in Elasticsearch
```bash
# Check if indices exist
curl http://localhost:9200/_cat/indices

# Check Logstash pipeline
curl http://localhost:9600/_node/stats/pipelines

# Generate test logs
./monitoring/test-elk.sh
```

### Debug Commands

```bash
# Check all service status
docker-compose -f docker-compose.dev.yml ps

# View all logs
docker-compose -f docker-compose.dev.yml logs

# Check Elasticsearch indices
curl http://localhost:9200/_cat/indices?v

# Check Logstash pipeline stats
curl http://localhost:9600/_node/stats/pipelines

# Test Elasticsearch query
curl -X GET "localhost:9200/fauxdan-logs-*/_search?size=1&sort=@timestamp:desc"
```

## Performance Tuning

### Elasticsearch
- **Memory**: Increase heap size for better performance
- **Indices**: Use daily indices with appropriate retention
- **Shards**: Single shard for development environment

### Logstash
- **Memory**: Adjust heap size based on log volume
- **Workers**: Increase worker threads for high throughput
- **Batch Size**: Optimize batch size for better performance

### Kibana
- **Refresh**: Adjust refresh interval for real-time monitoring
- **Queries**: Optimize queries for better performance
- **Visualizations**: Use appropriate aggregation levels

## Security Considerations

### Development Environment
- **Security Disabled**: X-Pack security is disabled for easy setup
- **Network Access**: Services are accessible from localhost only
- **Data Persistence**: Logs are stored in Docker volumes

### Production Recommendations
- **Enable Security**: Enable X-Pack security features
- **Network Security**: Use proper network segmentation
- **Authentication**: Implement proper authentication
- **Encryption**: Enable TLS for all communications
- **Access Control**: Implement role-based access control

## Maintenance

### Daily Tasks
- **Monitor Log Volume**: Check for unusual log patterns
- **Review Errors**: Investigate ERROR level logs
- **Check Performance**: Monitor response times and throughput

### Weekly Tasks
- **Index Management**: Review and optimize indices
- **Dashboard Updates**: Update dashboards based on needs
- **Alert Tuning**: Adjust alert thresholds

### Monthly Tasks
- **Log Retention**: Review and adjust retention policies
- **Performance Review**: Analyze performance metrics
- **Security Review**: Review access logs and security events

## Resources

- [Elasticsearch Documentation](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html)
- [Logstash Documentation](https://www.elastic.co/guide/en/logstash/current/index.html)
- [Kibana Documentation](https://www.elastic.co/guide/en/kibana/current/index.html)
- [ELK Stack Tutorial](https://www.elastic.co/guide/en/elastic-stack/current/index.html)
