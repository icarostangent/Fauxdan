# Caddy with Docker Swarm: Load Balancing & SSL Termination

This document explains how Caddy integrates with Docker Swarm to provide load balancing and SSL termination for the Fauxdan platform.

## 🔄 Architecture Overview

### **How Caddy Works in Swarm**:

#### **1. Service Discovery & Load Balancing**:
- **Docker Swarm's Built-in LB**: Swarm provides built-in load balancing at the service level
- **Caddy's Role**: Acts as a reverse proxy that discovers services via Docker labels
- **Dual Layer**: Swarm handles inter-service load balancing, Caddy handles external traffic routing

#### **2. SSL Termination**:
- **Automatic Certificates**: Caddy automatically obtains and renews Let's Encrypt certificates
- **Shared Storage**: Certificates stored in shared volumes for HA across multiple Caddy instances
- **Edge Termination**: SSL terminates at the edge (Caddy), internal traffic is HTTP

### **Traffic Flow**:
## 🏗️ Configuration Components

### **1. Caddy Service Configuration**

```yaml
caddy:
  image: lucaslorentz/caddy-docker-proxy:alpine
  deploy:
    replicas: 2
    placement:
      constraints:
        - node.labels.node.type == swarm-edge
        - node.labels.ssl.termination == true
        - node.labels.load.balancer == true
    resources:
      limits:
        cpus: '0.5'
        memory: 512M
      reservations:
        cpus: '0.25'
        memory: 256M
    restart_policy:
      condition: on-failure
      delay: 5s
      max_attempts: 3
      window: 120s
    update_config:
      parallelism: 1
      delay: 10s
      failure_action: rollback
      order: start-first
  ports:
    - "80:80"
    - "443:443"
  volumes:
    # Shared certificate storage for HA
    - caddy_certs:/data
    - caddy_config:/config
    # Docker socket for service discovery
    - /var/run/docker.sock:/var/run/docker.sock:ro
  environment:
    - CADDY_INGRESS_NETWORKS=frontend
    - CADDY_DOCKER_CADDYFILE_PATH=/config/Caddyfile
    - CADDY_DOCKER_PROCESS_CADDYFILE=true
    - CADDY_DOCKER_UNSAFE_HTTPS=true
  networks:
    - frontend
    - backend
  configs:
    - caddy_config
  secrets:
    - caddy_email
  healthcheck:
    test: ["CMD", "caddy", "validate", "--config", "/config/Caddyfile"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 40s
```

### **2. Service Labels for Caddy**

#### **Frontend Service**:
```yaml
frontend:
  image: nginx:alpine
  deploy:
    replicas: 2
    placement:
      constraints:
        - node.labels.node.type == swarm-edge
        - node.labels.workload.type == frontend
    labels:
      # Caddy configuration via labels
      caddy: "fauxdan.io,www.fauxdan.io"
      caddy.reverse_proxy: "{{upstreams}}"
      caddy.tls: "{{.Host}}"
      caddy.rewrite: "/{path} /"
      caddy.header: "X-Forwarded-Proto {scheme}"
      caddy.header: "X-Forwarded-For {remote}"
      caddy.header: "X-Real-IP {remote}"
  networks:
    - frontend
```

#### **Backend API Service**:
```yaml
backend:
  image: django:latest
  deploy:
    replicas: 3
    placement:
      constraints:
        - node.labels.node.type == swarm-worker
        - node.labels.workload.type == backend
    labels:
      # Caddy configuration for API
      caddy: "api.fauxdan.io"
      caddy.reverse_proxy: "{{upstreams}}"
      caddy.tls: "{{.Host}}"
      caddy.rewrite: "/api/{path} /{path}"
      caddy.header: "X-Forwarded-Proto {scheme}"
      caddy.header: "X-Forwarded-For {remote}"
      caddy.header: "X-Real-IP {remote}"
      caddy.header: "Access-Control-Allow-Origin *"
      caddy.header: "Access-Control-Allow-Methods GET,POST,PUT,DELETE,OPTIONS"
      caddy.header: "Access-Control-Allow-Headers Content-Type,Authorization"
  networks:
    - frontend
    - backend
```

## 🔄 Load Balancing Strategy

### **Layer 1: Caddy (Edge)**
- Routes external traffic based on domain/path
- Handles SSL termination
- Distributes to Swarm services
- **Load Balancing Method**: Round-robin by default

### **Layer 2: Docker Swarm**
- Load balances across service replicas
- Health checks and failover
- Service discovery via DNS
- **Load Balancing Method**: Built-in swarm load balancer

### **Load Balancing Flow**:
1. **External Request**: `https://api.fauxdan.io/api/users`
2. **Caddy**: Routes to backend service based on domain
3. **Swarm LB**: Distributes across backend replicas (3 instances)
4. **Backend**: Processes request, returns response
5. **Caddy**: Adds headers, returns HTTPS response

## 🔐 SSL Certificate Management

### **High Availability Setup**:

#### **1. Shared Volume Configuration**:
```yaml
volumes:
  caddy_certs:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /opt/caddy/certs
```

#### **2. Certificate Storage**:
- **Location**: `/data` volume mounted on all Caddy instances
- **Format**: Let's Encrypt certificates in standard format
- **Sharing**: All Caddy instances access same certificates
- **Backup**: Certificates persist across container restarts

#### **3. Automatic Renewal**:
- **Let's Encrypt**: Automatic certificate renewal
- **Validation**: HTTP-01 challenge via port 80
- **Renewal**: Happens automatically before expiration
- **Distribution**: New certificates available to all instances

## 🌐 Network Architecture

### **Frontend Network** (Public):
```yaml
networks:
  frontend:
    driver: overlay
    attachable: true
    external: false
```

**Services on Frontend Network**:
- Caddy instances (edge nodes)
- Frontend services (Vue.js)
- External access points

### **Backend Network** (Internal):
```yaml
networks:
  backend:
    driver: overlay
    internal: true
    external: false
```

**Services on Backend Network**:
- Backend services (Django)
- Database (PostgreSQL)
- Cache (Redis)
- Internal communication

## 🚀 Service Discovery

### **Docker Labels Approach**:

#### **Label Structure**:
```yaml
labels:
  caddy: "domain.com"                    # Target domain
  caddy.reverse_proxy: "{{upstreams}}"   # Upstream services
  caddy.tls: "{{.Host}}"                 # TLS configuration
  caddy.rewrite: "/api/{path} /{path}"   # URL rewriting
  caddy.header: "Header-Name {value}"    # Custom headers
```

#### **Dynamic Discovery**:
- **Automatic**: Services discovered via Docker labels
- **Real-time**: Changes applied without restart
- **Flexible**: Easy to add/remove services
- **Declarative**: Configuration in compose file

## 🔧 Best Practices

### **1. High Availability**:
- Deploy Caddy on multiple edge nodes
- Use shared certificate storage
- Implement proper health checks
- Configure rolling updates

### **2. Security**:
- Internal services use HTTP (behind Caddy)
- External traffic always HTTPS
- Proper firewall rules
- Network segmentation

### **3. Performance**:
- Caddy instances on edge nodes only
- Backend services on worker nodes
- Database on storage nodes
- Resource limits and reservations

## ��️ Troubleshooting

### **Common Issues**:

#### **1. Certificate Problems**:
```bash
# Check certificate status
docker exec caddy caddy list-certificates

# Validate configuration
docker exec caddy caddy validate --config /config/Caddyfile
```

#### **2. Service Discovery Issues**:
```bash
# Check service labels
docker service inspect <service-name> --format "{{.Spec.Labels}}"

# Verify network connectivity
docker exec caddy ping <service-name>
```

#### **3. Load Balancing Problems**:
```bash
# Check service replicas
docker service ps <service-name>

# Verify health status
docker service inspect <service-name> --format "{{.Spec.TaskTemplate.ContainerSpec.Healthcheck}}"
```

This configuration provides robust load balancing, automatic SSL management, and high availability for your Fauxdan platform!