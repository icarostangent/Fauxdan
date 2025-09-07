# Docker Swarm Node Labels

This document describes the comprehensive node labeling system implemented for the Fauxdan Docker Swarm infrastructure.

## Label Categories

### Master Node Labels
- `role=master` - Node role identifier
- `tier=management` - Management tier
- `node.type=swarm-master` - Node type identifier

### Edge Node Labels
- `role=edge` - Node role identifier
- `tier=public` - Public-facing tier
- `node.type=swarm-edge` - Node type identifier
- `service.placement=edge` - Service placement hint
- `network.exposure=public` - Network exposure level
- `workload.type=frontend` - Workload type
- `ssl.termination=true` - SSL termination capability
- `load.balancer=true` - Load balancer capability

### Worker Node Labels
- `role=worker` - Node role identifier
- `tier=application` - Application tier
- `node.type=swarm-worker` - Node type identifier
- `service.placement=worker` - Service placement hint
- `network.exposure=internal` - Network exposure level
- `workload.type=backend` - Workload type
- `scaling.enabled=true` - Auto-scaling capability
- `monitoring.enabled=true` - Monitoring capability

### Storage Node Labels
- `role=storage` - Node role identifier
- `tier=persistence` - Data persistence tier
- `node.type=swarm-storage` - Node type identifier
- `service.placement=storage` - Service placement hint
- `network.exposure=internal` - Network exposure level
- `workload.type=database` - Workload type
- `storage.type=persistent` - Storage type
- `backup.enabled=true` - Backup capability
- `data.critical=true` - Critical data indicator

## Service Placement Examples

### Deploy to Edge Nodes Only
```yaml
services:
  caddy:
    image: caddy:2-alpine
    deploy:
      placement:
        constraints:
          - node.labels.node.type == swarm-edge
          - node.labels.ssl.termination == true
```

### Deploy to Worker Nodes Only
```yaml
services:
  backend:
    image: django:latest
    deploy:
      placement:
        constraints:
          - node.labels.node.type == swarm-worker
          - node.labels.workload.type == backend
```

### Deploy to Storage Nodes Only
```yaml
services:
  postgres:
    image: postgres:13
    deploy:
      placement:
        constraints:
          - node.labels.node.type == swarm-storage
          - node.labels.storage.type == persistent
```

### Complex Placement Rules
```yaml
services:
  monitoring:
    image: prometheus:latest
    deploy:
      placement:
        constraints:
          - node.labels.node.type == swarm-worker
          - node.labels.monitoring.enabled == true
          - node.labels.scaling.enabled == true
```

## Label-Based Service Distribution

### Frontend Services (Edge Nodes)
- **Caddy Proxy**: SSL termination, load balancing
- **Vue.js Frontend**: Static assets, SPA
- **SSL Certificates**: Let's Encrypt automation

### Backend Services (Worker Nodes)
- **Django API**: REST API services
- **Scanner Service**: Masscan integration
- **Redis Cache**: Session management
- **Monitoring Stack**: Prometheus, Grafana

### Storage Services (Storage Nodes)
- **PostgreSQL**: Primary database
- **Elasticsearch**: Log storage and search
- **Backup Services**: Automated backups

## Management Commands

### View Node Labels
```bash
# List all nodes with labels
docker node ls --format "table {{.ID}}\t{{.Hostname}}\t{{.Status}}\t{{.Availability}}\t{{.ManagerStatus}}"

# Inspect specific node labels
docker node inspect <node-id> --format "{{range \$key, \$value := .Spec.Labels}}{{\$key}}={{\$value}} {{end}}"
```

### Update Node Labels
```bash
# Add a new label
docker node update --label-add <key>=<value> <node-id>

# Remove a label
docker node update --label-rm <key> <node-id>
```

### Service Placement Verification
```bash
# Check where services are deployed
docker service ps <service-name> --format "table {{.Name}}\t{{.Node}}\t{{.CurrentState}}"

# List all services and their placement
docker service ls --format "table {{.Name}}\t{{.Replicas}}\t{{.Image}}"
```

## Best Practices

1. **Use Multiple Constraints**: Combine multiple label constraints for precise placement
2. **Resource Limits**: Always set resource limits for services
3. **Health Checks**: Implement health checks for all services
4. **Rolling Updates**: Use rolling update strategies for zero-downtime deployments
5. **Monitoring**: Deploy monitoring services to nodes with `monitoring.enabled=true`

## Troubleshooting

### Service Not Starting
```bash
# Check service logs
docker service logs <service-name>

# Check service constraints
docker service inspect <service-name> --format "{{.Spec.TaskTemplate.Placement.Constraints}}"
```

### Node Availability
```bash
# Check node availability
docker node ls

# Drain a node (maintenance)
docker node update --availability drain <node-id>

# Make node available again
docker node update --availability active <node-id>
```

### Label Verification
```bash
# Verify all node labels
for node in $(docker node ls -q); do
  echo "Node: $node"
  docker node inspect $node --format "{{range \$key, \$value := .Spec.Labels}}{{\$key}}={{\$value}} {{end}}"
  echo ""
done
```
