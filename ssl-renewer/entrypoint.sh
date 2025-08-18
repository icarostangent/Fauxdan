#!/bin/bash

set -e

echo "Starting SSL renewal service..."

# Set default values if not provided
RENEWAL_INTERVAL=${RENEWAL_INTERVAL:-"0 12 * * *"}
DOMAIN_NAME=${DOMAIN_NAME:-"fauxdan.io"}
COMPOSE_PROJECT_NAME=${COMPOSE_PROJECT_NAME:-"fauxdan"}

echo "Configuration:"
echo "  Renewal interval: $RENEWAL_INTERVAL"
echo "  Domain name: $DOMAIN_NAME"
echo "  Compose project: $COMPOSE_PROJECT_NAME"

# Wait for Docker socket to be available
echo "Waiting for Docker socket..."
while [ ! -S /var/run/docker.sock ]; do
    echo "Docker socket not available, waiting..."
    sleep 5
done

# Wait for certbot service to be available
echo "Waiting for certbot service..."
while ! docker ps --format "{{.Names}}" | grep -q "${COMPOSE_PROJECT_NAME}-certbot-1"; do
    echo "Certbot service not available, waiting..."
    sleep 5
done

# Wait for nginx service to be available
echo "Waiting for nginx service..."
while ! docker ps --format "{{.Names}}" | grep -q "${COMPOSE_PROJECT_NAME}-nginx-1"; do
    echo "Nginx service not available, waiting..."
    sleep 5
done

echo "All required services are available!"

# Set up cron job
echo "Setting up cron job for SSL renewal..."
echo "$RENEWAL_INTERVAL /usr/local/bin/renew-ssl.sh" > /etc/crontabs/root

# Start cron daemon in background
echo "Starting cron daemon..."
crond -f -d 8 &

# Wait for cron to start
sleep 2

# Verify cron is running
if pgrep crond > /dev/null; then
    echo "Cron daemon started successfully"
    echo "SSL renewal cron job configured: $RENEWAL_INTERVAL"
    echo "SSL renewal service is ready!"
else
    echo "Failed to start cron daemon"
    exit 1
fi

# Keep container running
echo "SSL renewal service is running. Press Ctrl+C to stop."
trap 'echo "Stopping SSL renewal service..."; exit 0' SIGTERM SIGINT

# Wait indefinitely
while true; do
    sleep 3600
done
