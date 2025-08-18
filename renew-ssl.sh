#!/bin/bash

# SSL certificate renewal script following PhoenixNAP strategy
# This script can be run manually or as a cron job

set -e

echo "Renewing Let's Encrypt certificates..."

# Renew certificates
docker-compose -f docker-compose.prod.yml run --rm certbot renew

if [ $? -eq 0 ]; then
    echo "Certificates renewed successfully!"
    echo "Reloading nginx configuration..."
    
    # Reload nginx to pick up new certificates
    docker-compose -f docker-compose.prod.yml exec webserver nginx -s reload
    
    echo "SSL renewal completed successfully!"
else
    echo "Failed to renew certificates"
    exit 1
fi
