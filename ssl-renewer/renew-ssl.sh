#!/bin/bash

# SSL renewal script for automatic Let's Encrypt certificate renewal
# This script is executed by cron inside the ssl-renewer container

set -e

# Configuration
DOMAIN_NAME=${DOMAIN_NAME:-"fauxdan.io"}
COMPOSE_PROJECT_NAME=${COMPOSE_PROJECT_NAME:-"fauxdan"}
LOG_FILE="/var/log/ssl-renewal.log"

# Log function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Start renewal process
log "Starting SSL certificate renewal process"

# Check if we're running in the right container
if [ ! -S /var/run/docker.sock ]; then
    log "ERROR: Docker socket not available"
    exit 1
fi

# Check if certbot service is running
if ! docker ps --format "{{.Names}}" | grep -q "${COMPOSE_PROJECT_NAME}-certbot-1"; then
    log "ERROR: Certbot service is not running"
    exit 1
fi

# Check if nginx service is running
if ! docker ps --format "{{.Names}}" | grep -q "${COMPOSE_PROJECT_NAME}-nginx-1"; then
    log "ERROR: Nginx service is not running"
    exit 1
fi

log "All required services are running"

# Attempt to renew certificates
log "Attempting to renew SSL certificates..."
if docker exec "${COMPOSE_PROJECT_NAME}-certbot-1" certbot renew --quiet; then
    log "SSL certificates renewed successfully"
    
    # Check if certificates were actually renewed
    if docker exec "${COMPOSE_PROJECT_NAME}-certbot-1" certbot certificates | grep -q "VALID:"; then
        log "Reloading nginx configuration to pick up renewed certificates..."
        
        # Reload nginx to pick up new certificates
        if docker exec "${COMPOSE_PROJECT_NAME}-nginx-1" nginx -s reload; then
            log "Nginx configuration reloaded successfully"
            log "SSL renewal process completed successfully"
        else
            log "ERROR: Failed to reload nginx configuration"
            exit 1
        fi
    else
        log "No certificates found or certificates are invalid"
        exit 1
    fi
else
    log "ERROR: Failed to renew SSL certificates"
    exit 1
fi

log "SSL renewal process completed"
