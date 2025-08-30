---
title: Streamlining CI/CD with GitLab and Docker Compose
date: 2025-08-30
author: Fauxdan DevOps Team
tags: [ci-cd, gitlab, docker, devops, automation]
excerpt: Discover how we simplified our CI/CD pipeline by leveraging Docker Compose for building and deploying containerized applications, achieving faster deployments and better reliability.
---

# Streamlining CI/CD with GitLab and Docker Compose

In the world of modern software development, the ability to quickly and reliably deploy code changes is crucial. Our journey to optimize the Fauxdan CI/CD pipeline led us to a powerful combination: GitLab CI/CD with Docker Compose integration. The results? **Faster deployments, improved reliability, and a much simpler pipeline to maintain.**

## The Problem: Complex, Slow Deployments

When we first implemented our CI/CD pipeline, we followed a common pattern: build Docker images directly in the deployment step using individual `docker build` commands. While this approach worked, it had several significant drawbacks:

### **Performance Issues**
- **Deployment time**: 15-20 minutes per deployment
- **Network overhead**: Large Docker images transferred during deployment
- **Resource contention**: Building and deploying competed for the same resources
- **No caching**: Every deployment rebuilt images from scratch

### **Maintenance Complexity**
- **Duplicated configuration**: Build settings repeated in CI and Docker Compose files
- **Hard to debug**: Build failures mixed with deployment issues
- **Difficult to scale**: Adding new services required pipeline modifications
- **Version management**: Manual tagging and versioning of images

### **Reliability Concerns**
- **Single point of failure**: Build and deploy in one step
- **Rollback complexity**: No easy way to revert to previous working images
- **Resource conflicts**: Build processes could interfere with deployment

## The Solution: Separated Build and Deploy

We restructured our pipeline into three distinct stages:

```
provision → build → deploy
   ↓         ↓       ↓
  ~2min    ~8min   ~3min
```

### **Stage 1: Provision**
Infrastructure setup and server preparation using Ansible.

### **Stage 2: Build** 
Docker image building and registry pushing using Docker Compose.

### **Stage 3: Deploy**
Application deployment using pre-built images.

## Implementation: Docker Compose Integration

### **The Build Stage**

Our build stage is remarkably simple yet powerful:

```yaml
build:production:
  stage: build
  before_script:
    - echo "$GITLAB_REGISTRY_PASSWORD" | docker login gitlab.icarostangent.lab:5050 -u $GITLAB_REGISTRY_USERNAME --password-stdin
  script:
    - docker compose -f docker-compose.build.yml pull
    - docker compose -f docker-compose.build.yml build
    - docker compose -f docker-compose.build.yml push
    - docker system prune -f
  only:
    - master
  tags:
    - docker
```

**Key Benefits:**
- **Leverages existing configuration**: Uses our `docker-compose.build.yml` file
- **Single command builds**: One `docker compose build` builds all services
- **Automatic dependency management**: Docker Compose handles build order and dependencies
- **Consistent with development**: Same build process locally and in CI

### **Docker Compose Build Configuration**

Our `docker-compose.build.yml` defines all build configurations:

```yaml
services:
  backend:
    image: gitlab.icarostangent.lab:5050/josh/fauxdan/backend
    build:
      context: ./backend
      dockerfile: Dockerfile.prod.backend
      
  scanner:
    image: gitlab.icarostangent.lab:5050/josh/fauxdan/scanner
    build:
      context: ./backend
      dockerfile: Dockerfile.prod.scanner

  caddy: 
    image: gitlab.icarostangent.lab:5050/josh/fauxdan/caddy
    build:
      context: ./
      dockerfile: ./caddy/Dockerfile
      args:
        VUE_APP_API_URL: ${VUE_APP_API_URL}

  tor:
    image: gitlab.icarostangent.lab:5050/josh/fauxdan/tor
    build:
      context: ./tor
      dockerfile: Dockerfile
```

## Performance Improvements: The Numbers

### **Deployment Time Reduction**

| Metric | Before (Combined) | After (Separated) | Improvement |
|--------|------------------|-------------------|-------------|
| **Total Pipeline Time** | 17-22 minutes | 13 minutes | **35-40% faster** |
| **Deploy Step Time** | 15-20 minutes | 3 minutes | **75-80% faster** |
| **Build Step Time** | N/A | 8 minutes | New capability |
| **Provision Step Time** | 2 minutes | 2 minutes | No change |

### **Resource Utilization**

- **Build stage**: Runs on Docker-enabled runners with full build capabilities
- **Deploy stage**: Runs on lightweight runners (just needs Ansible)
- **Parallel execution**: Build and provision can run simultaneously
- **Better caching**: Docker layer caching and registry optimization

## Key Benefits Beyond Performance

### **1. Improved Reliability**

**Before**: Single point of failure - if builds failed, deployment never started
**After**: Build failures are caught early, deployment only runs with valid images

```yaml
deploy:production:
  needs:
    - provision
    - build:production  # Only deploy if build succeeds
```

### **2. Better Rollback Capability**

**Before**: Rollbacks required rebuilding images
**After**: Quick rollback using pre-built images with commit tags

```bash
# Rollback to previous version
docker pull gitlab.icarostangent.lab:5050/josh/fauxdan/backend:abc123
docker tag gitlab.icarostangent.lab:5050/josh/fauxdan/backend:abc123 latest
```

### **3. Easier Debugging**

**Before**: Build and deployment issues mixed together
**After**: Clear separation - build issues in build stage, deployment issues in deploy stage

### **4. Scalability**

**Before**: Adding new services required pipeline modifications
**After**: Just add to `docker-compose.build.yml` - pipeline automatically handles it

## Implementation Best Practices

### **1. Use Docker Compose for Everything**

```yaml
# Instead of individual docker commands
- docker build -t service1 ./service1
- docker build -t service2 ./service2

# Use Docker Compose
- docker compose -f docker-compose.build.yml build
```

### **2. Leverage Build Arguments**

```yaml
# Pass environment variables to builds
caddy:
  build:
    args:
      VUE_APP_API_URL: ${VUE_APP_API_URL}
```

### **3. Implement Proper Tagging**

```yaml
# Tag with both latest and commit SHA
- docker tag service:latest service:$CI_COMMIT_SHA
- docker push service:latest
- docker push service:$CI_COMMIT_SHA
```

### **4. Clean Up Resources**

```yaml
# Prevent disk space issues
- docker system prune -f
```

## Common Pitfalls and Solutions

### **1. Docker-in-Docker Complexity**

**Problem**: Complex DinD setup with TLS certificates
**Solution**: Use host Docker on runners with Docker support

```yaml
# Simple approach - no DinD needed
build:production:
  tags:
    - docker  # Runner with Docker installed
```

### **2. Build Context Issues**

**Problem**: Large build contexts slow down builds
**Solution**: Use `.dockerignore` files and optimize contexts

```dockerfile
# .dockerignore
node_modules/
.git/
*.log
.env
```

### **3. Registry Authentication**

**Problem**: Authentication failures during builds
**Solution**: Use GitLab CI/CD variables and proper login

```yaml
before_script:
  - echo "$GITLAB_REGISTRY_PASSWORD" | docker login gitlab.icarostangent.lab:5050 -u $GITLAB_REGISTRY_USERNAME --password-stdin
```

## Monitoring and Optimization

### **Pipeline Metrics to Track**

- **Build time per service**: Identify slow-building services
- **Image size trends**: Monitor for bloat
- **Registry pull times**: Optimize network performance
- **Cache hit rates**: Ensure Docker layer caching is working

### **Continuous Improvement**

- **Regular review**: Analyze pipeline performance monthly
- **Image optimization**: Optimize Dockerfiles for faster builds
- **Parallel builds**: Build independent services in parallel
- **Registry optimization**: Use local registries for faster pulls

## The Future: Advanced Optimizations

### **Multi-Stage Builds**

```dockerfile
# Optimize image sizes
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
```

### **Parallel Service Building**

```yaml
# Build independent services in parallel
build:backend:
  script:
    - docker compose -f docker-compose.build.yml build backend

build:frontend:
  script:
    - docker compose -f docker-compose.build.yml build caddy
```

### **Advanced Caching**

```yaml
# Use BuildKit for better caching
variables:
  DOCKER_BUILDKIT: 1
  COMPOSE_DOCKER_CLI_BUILD: 1
```

## Conclusion

The transition to a separated build and deploy pipeline using Docker Compose has transformed our CI/CD process. What started as a 20-minute deployment process is now a streamlined 13-minute pipeline with better reliability, easier maintenance, and improved debugging capabilities.

**Key Takeaways:**

1. **Separation of concerns** improves both performance and reliability
2. **Docker Compose integration** reduces configuration duplication
3. **Proper staging** enables better resource utilization
4. **Image caching** significantly reduces deployment time
5. **Simplified maintenance** makes the pipeline easier to scale

The beauty of this approach is its simplicity. By leveraging existing Docker Compose configurations and separating build from deployment, we've created a pipeline that's not only faster but also more maintainable and reliable.

For teams looking to optimize their CI/CD pipelines, the combination of GitLab CI/CD with Docker Compose provides an excellent balance of performance, simplicity, and maintainability. The investment in restructuring pays dividends in faster deployments, better reliability, and reduced operational overhead.

---

*Ready to optimize your own CI/CD pipeline? Start by identifying your current bottlenecks and consider how separating build and deploy stages could improve your deployment process.*
