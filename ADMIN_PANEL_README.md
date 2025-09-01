# 🚀 Fauxdan Admin Panel

This document describes the new admin panel setup for the Fauxdan project, which provides centralized access to Django admin, Grafana dashboards, and Prometheus monitoring.

## 🏗️ Architecture Overview

The admin panel consists of two main services:

1. **`caddy-admin`** - Reverse proxy service that routes requests to appropriate backend services
2. **`backend-admin`** - Django backend service running on port 8001 for admin functionality

### Service Ports

- **Main Admin Panel**: `https://localhost:8443`
- **Django Admin**: `https://localhost:8443/admin`
- **Grafana**: `https://localhost:8443/grafana`
- **Prometheus**: `https://localhost:8443/prometheus`
- **Backend Admin API**: `https://localhost:8443/api/` (if needed)

## 🚀 Quick Start

### 1. Start Admin Services

```bash
# Start only the admin services
./start-admin-services.sh

# Or manually start them
docker compose --env-file .env.dev -f docker-compose.dev.yml up -d caddy-admin backend-admin
```

### 2. Access the Admin Panel

Open your browser and navigate to: **https://localhost:8443**

You'll see a beautiful admin dashboard with cards for each service.

### 3. Access Individual Services

- **Django Admin**: https://localhost:8443/admin
- **Grafana**: https://localhost:8443/grafana
- **Prometheus**: https://localhost:8443/prometheus

## 🔧 Configuration Files

### Caddy Admin Configuration

**File**: `caddy/Caddyfile.admin.dev`

This configuration handles routing for the admin panel:
- Routes `/admin/*` to the Django backend-admin service
- Routes `/grafana/*` to the Grafana service
- Routes `/prometheus/*` to the Prometheus service
- Serves the admin index page at the root

### Grafana Configuration

**File**: `monitoring/grafana/provisioning/grafana/grafana.ini`

Updated to work with subpath deployment:
- `root_url = https://localhost:8443/grafana/`
- `serve_from_sub_path = true`

### Docker Compose Updates

**File**: `docker-compose.dev.yml`

New services added:
- `caddy-admin`: Admin panel reverse proxy
- `backend-admin`: Django admin backend

## 📁 File Structure

```
monitoring/
├── admin/
│   └── index.html          # Admin panel main page
├── grafana/
│   ├── dashboards/
│   │   └── admin/          # Admin-specific dashboards
│   └── provisioning/
│       ├── dashboards/
│       │   └── admin-dashboards.yml
│       └── grafana/
│           └── grafana.ini
caddy/
├── Caddyfile.dev           # Main app routing
└── Caddyfile.admin.dev     # Admin panel routing
```

## 🎯 Key Features

### 1. **Centralized Access**
- Single entry point for all admin functions
- Beautiful, responsive interface
- Service status indicators

### 2. **Service Routing**
- Django admin at `/admin`
- Grafana dashboards at `/grafana`
- Prometheus metrics at `/prometheus`
- Clean URL structure

### 3. **Security**
- Separate admin network
- Isolated admin services
- Development-friendly configuration

## 🔍 Troubleshooting

### Common Issues

#### 1. **Services Not Starting**
```bash
# Check service status
docker compose --env-file .env.dev -f docker-compose.dev.yml ps

# View logs
docker compose --env-file .env.dev -f docker-compose.dev.yml logs caddy-admin
docker compose --env-file .env.dev -f docker-compose.dev.yml logs backend-admin
```

#### 2. **Port Conflicts**
If port 8080 is already in use:
```bash
# Find what's using the port
sudo lsof -i :8080

# Or change the port in docker-compose.dev.yml
ports:
  - "8081:80"  # Change 8080 to 8081
```

#### 3. **Grafana Not Loading**
Check Grafana configuration:
```bash
# Verify Grafana is running
docker compose --env-file .env.dev -f docker-compose.dev.yml logs grafana

# Check if subpath is working
curl http://localhost:8080/grafana/api/health
```

### Service Management

```bash
# Start all admin services
docker compose --env-file .env.dev -f docker-compose.dev.yml up -d

# Stop admin services
docker compose --env-file .env.dev -f docker-compose.dev.yml stop caddy-admin backend-admin

# Restart admin services
docker compose --env-file .env.dev -f docker-compose.dev.yml restart caddy-admin backend-admin

# View all logs
docker compose --env-file .env.dev -f docker-compose.dev.yml logs -f
```

## 🔄 Development Workflow

### 1. **Making Changes**
- Edit configuration files
- Restart affected services
- Test changes in browser

### 2. **Adding New Services**
1. Add service to `docker-compose.dev.yml`
2. Add routing in `Caddyfile.admin.dev`
3. Update admin index page if needed
4. Restart services

### 3. **Updating Dashboards**
1. Place dashboard JSON files in `monitoring/grafana/dashboards/admin/`
2. Restart Grafana service
3. Access via `/grafana` subpath

## 🌐 Production Considerations

For production deployment:

1. **Security**: Enable HTTPS, add authentication
2. **Monitoring**: Add health checks and alerting
3. **Backup**: Configure backup for admin data
4. **Scaling**: Consider load balancing for high traffic

## 📚 Additional Resources

- [Caddy Documentation](https://caddyserver.com/docs/)
- [Grafana Subpath Configuration](https://grafana.com/docs/grafana/latest/setup-grafana/configure-grafana/)
- [Django Admin Documentation](https://docs.djangoproject.com/en/stable/ref/contrib/admin/)

## 🤝 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review service logs
3. Verify configuration files
4. Check port availability

---

**Happy Administering! 🎉**
