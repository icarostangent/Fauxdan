# Fauxdan - Elite Internet Intelligence Platform

**Fauxdan** is a sophisticated network reconnaissance and intelligence gathering platform that combines cybersecurity learning with community service. It provides comprehensive network scanning capabilities while maintaining ethical scanning practices.

## 🎯 Mission

Fauxdan exists at the intersection of learning and contribution. While developing cybersecurity expertise, it simultaneously provides the community with valuable network intelligence that enhances collective security awareness.

## 🏗️ Architecture

### Core Components

- **Backend**: Django REST API with PostgreSQL for data persistence
- **Frontend**: Vue.js 3 with TypeScript and modern UI/UX design
- **Scanner**: Custom integration with Masscan for high-performance port discovery
- **Infrastructure**: Docker-based microservices deployment with Redis caching
- **Monitoring**: Prometheus, Grafana, Elasticsearch, Logstash, and Kibana stack

### Services

- **Backend**: Main API server (`backend:8000`)
- **Backend-Admin**: Admin-specific functionality (`backend-admin:8000`)
- **Scanner**: Background port scanning service with NET_ADMIN capabilities
- **Database**: PostgreSQL with health checks and automated backups
- **Cache**: Redis for session management and caching
- **Proxy**: Caddy reverse proxy with SSL termination
- **Tor**: Anonymous scanning capabilities
- **Monitoring**: Full observability stack with metrics, logs, and dashboards

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Git access to the repository
- Environment variables configured

### Environment Setup

1. Copy the environment template:
   ```bash
   cp env.template .env
   ```

2. Configure required variables in `.env`:
   - Database credentials
   - Django secret key
   - Domain configuration
   - SSL certificate settings

### Deployment
#### Development Environment
```bash
docker compose -f docker-compose.dev.yml --env-file .env.dev up -d
```

#### Staging Environment
```bash
docker compose -f docker-compose.staging.yml --env-file .env up -d
```

#### Production Environment
```bash
docker compose -f docker-compose.prod.yml --env-file .env up -d
```

### Health Checks

- Main API: `https://staging.fauxdan.io/api/health/`
- Admin Panel: `https://staging-admin.fauxdan.io:8443/`
- Monitoring: `https://staging-admin.fauxdan.io:8443/grafana/`

## 🔍 Core Functionality

### Port Scanning

**Masscan Integration**: High-performance port discovery using industry-standard tools with:
- TCP, UDP, and SYN scanning capabilities
- Configurable scan rates (default: 7,500 packets/second)
- Comprehensive port coverage (HTTP, databases, mail, FTP, DNS, Docker, Kubernetes, proxies, LDAP, RPC, monitoring, VPN, NoSQL)
- Proxy support via proxychains for anonymous scanning

### Domain Enumeration

- **Reverse DNS Lookup**: Automated hostname discovery from IP addresses
- **SSL Certificate Analysis**: Domain extraction from SSL certificates (CN and SAN fields)
- **Smart Targeting**: Focuses on web ports (80, 443) for domain discovery
- **Duplicate Prevention**: 2-week cooldown to prevent redundant scans

### Data Management

- **Host Discovery**: IP address tracking with last-seen timestamps
- **Port Tracking**: Open port monitoring with service identification
- **Domain Mapping**: SSL certificate-based domain discovery
- **Proxy Validation**: SOCKS4, SOCKS5, HTTP, and HTTPS proxy support

## 🎮 Control & Management

### Management Commands

#### Port Scanning
```bash
# Basic port scan
docker compose -f docker-compose.dev.yml --env-file .env run scanner python3 manage.py run_masscan --target=192.168.1.0/24

# Custom port range
python manage.py run_masscan --target=10.0.0.1 --ports=80,443,8080

# Protocol-specific scanning
python manage.py run_masscan --target=192.168.1.1 --tcp --udp --syn

# Anonymous scanning via proxy
python manage.py run_masscan --target=target.com --use_proxychains
```

#### Domain Enumeration
```bash
# Enumerate domains for a specific host
python manage.py schedule_enumerate_domains --target=host_id

# Direct domain enumeration
python manage.py enumerate_domains --target=192.168.1.1
```

#### Maintenance
```bash
# Clean up old port data
python manage.py cleanup_old_ports

# Update timestamps
python manage.py update_timestamps

# Test proxy connectivity
python manage.py check_proxy --proxy=proxy:port
```

### API Endpoints

#### Core Data Access
- `GET /api/scans/` - List all scans
- `GET /api/hosts/` - List discovered hosts
- `GET /api/ports/` - List open ports
- `GET /api/domains/` - List discovered domains
- `GET /api/proxies/` - List proxy servers

#### Scan Management
- `POST /api/create-scan/` - Scanner only endpoint
  - `scan_type`: `port_scan` or `enumerate_domains`
  - `target`: IP address or hostname
  - `ports`: Optional port list

#### Search & Discovery
- `GET /api/search/` - Universal search across all data
- `GET /api/dnsrelays/` - DNS relay information

#### Health & Monitoring
- `GET /api/health/` - Application health check
- `GET /metrics/` - Prometheus metrics
- `GET /metrics/health/` - Metrics health check

### Web Interface

- **Main Dashboard**: `https://staging.fauxdan.io/`
- **API Documentation**: `https://staging.fauxdan.io/api/`
- **Admin Panel**: `https://staging.admin.icarostangent.lab:8443/`
- **Dev Admin Panel (requires port forward)**: `https://localhost:8443/`
- **Monitoring Dashboards**: `https://staging-admin.fauxdan.io:8443/grafana/`

## 🔧 Configuration

### Scan Configuration

The scanner supports extensive configuration through the `MasscanConfigurator` class:

- **Rate Limiting**: Configurable scan rates for responsible scanning
- **Port Selection**: Predefined port lists or custom port ranges
- **Protocol Support**: TCP, UDP, and SYN scanning
- **Proxy Integration**: Anonymous scanning via proxychains
- **Resume Capability**: Resume interrupted scans

### Environment Variables

Key configuration options in `.env`:

```bash
# Database
DJANGO_DB_NAME=fauxdan
DJANGO_DB_USER=fauxdan
DJANGO_DB_PASSWORD=your_password
DJANGO_DB_HOST=db
DJANGO_DB_PORT=5432

# Security
DJANGO_SECRET_KEY=your_secret_key
DJANGO_DEBUG=False

# Domain & SSL
DOMAIN_NAME=fauxdan.io
LETSENCRYPT_EMAIL=your@email.com

# API
VUE_APP_API_URL=https://fauxdan.io
```

## 📊 Monitoring & Observability

### Metrics
- **Prometheus**: System and application metrics
- **Grafana**: Custom dashboards and visualization
- **Node Exporter**: System resource monitoring
- **Redis/Postgres Exporters**: Service-specific metrics

### Logging
- **Elasticsearch**: Centralized log storage
- **Logstash**: Log processing and forwarding
- **Kibana**: Log analysis and visualization
- **Structured Logging**: JSON-formatted application logs

### Health Monitoring
- **Docker Health Checks**: Container-level health monitoring
- **API Health Endpoints**: Application-level health checks
- **Database Health**: PostgreSQL connection monitoring
- **Service Dependencies**: Inter-service health validation

## 🛡️ Security Features

- **Tor Integration**: Anonymous scanning capabilities
- **Proxy Support**: SOCKS4, SOCKS5, HTTP, and HTTPS proxies
- **SSL/TLS Handling**: Secure communication and certificate analysis
- **Rate Limiting**: Responsible scanning practices
- **Access Control**: JWT-based authentication
- **Network Isolation**: Docker-based service isolation

## 🚀 Deployment

### Automated Deployment

The platform includes comprehensive deployment automation:

- **Ansible Playbooks**: `deploy-application.yml` for automated deployment
- **GitLab CI/CD**: Automated build and deployment pipeline
- **Docker Registry**: Private container registry integration
- **Health Checks**: Automated service validation

### Manual Deployment

1. **Clone Repository**:
   ```bash
   git clone <repository-url>
   cd fauxdan
   ```

2. **Configure Environment**:
   ```bash
   cp env.template .env
   # Edit .env with your configuration
   ```

3. **Deploy Services**:
   ```bash
   docker compose -f docker-compose.staging.yml --env-file .env up -d
   ```

4. **Verify Deployment**:
   ```bash
   curl https://staging.fauxdan.io/api/health/
   ```

## 📈 Performance

- **High-Speed Scanning**: Masscan integration for efficient port discovery
- **Asynchronous Processing**: Non-blocking scan execution
- **Database Optimization**: Indexed queries and efficient data structures
- **Caching**: Redis-based caching for improved performance
- **Load Balancing**: Caddy-based reverse proxy with load balancing

## 🤝 Contributing

Fauxdan serves dual purposes:
1. **Learning Platform**: Hands-on cybersecurity skill development
2. **Community Service**: Providing valuable network intelligence

The platform maintains a balance between aggressive intelligence gathering and responsible community citizenship, ensuring scans are designed to discover, not disrupt.

## 📝 License

This project is designed for educational and community service purposes. Please ensure all scanning activities comply with applicable laws and regulations.

---

*"The best way to learn is to do. The best way to serve is to share."*