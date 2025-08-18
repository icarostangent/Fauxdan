#!/bin/bash

# Setup script for Let's Encrypt SSL certificates following PhoenixNAP strategy
# This script helps with the initial certificate setup

set -e

echo "Setting up Let's Encrypt SSL certificates..."

# Check if domain is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <domain-name-or-ip>"
    echo "Example: $0 fauxdan.io"
    echo "Example: $0 192.168.1.100"
    exit 1
fi

DOMAIN=$1

echo "Setting up SSL for: $DOMAIN"

# Check if this is an IP address
if [[ $DOMAIN =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Warning: $DOMAIN appears to be an IP address."
    echo "Let's Encrypt requires a valid domain name for SSL certificates."
    echo "Please ensure you have a domain name pointing to this IP address."
    echo "Continuing with setup..."
fi

# Start the nginx service first
echo "Starting nginx service..."
docker-compose -f docker-compose.prod.yml up -d nginx

# Wait for webserver to be ready
echo "Waiting for webserver to be ready..."
sleep 10

# Test the webroot access
echo "Testing webroot access..."
if curl -s "http://$DOMAIN/.well-known/acme-challenge/test" > /dev/null 2>&1; then
    echo "Webroot is accessible"
else
    echo "Creating test file in webroot..."
    echo "test" > certbot/www/.well-known/acme-challenge/test
    echo "Test file created"
fi

# Run certbot dry run first
echo "Running certbot dry run..."
docker-compose -f docker-compose.prod.yml run --rm certbot certonly \
    --webroot \
    --webroot-path /var/www/certbot \
    --dry-run \
    -d $DOMAIN

if [ $? -eq 0 ]; then
    echo "Dry run successful! Now getting real certificates..."
    
    # Get real certificates
    docker-compose -f docker-compose.prod.yml run --rm certbot certonly \
        --webroot \
        --webroot-path /var/www/certbot \
        -d $DOMAIN
    
    if [ $? -eq 0 ]; then
        echo "Certificates obtained successfully!"
        echo "Now updating nginx configuration for HTTPS..."
        
        # Update nginx config to include HTTPS
        cat >> nginx/conf/app.conf << EOF

server {
    listen 443 default_server ssl http2;
    listen [::]:443 ssl http2;

    server_name $DOMAIN;

    ssl_certificate /etc/nginx/ssl/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/live/$DOMAIN/privkey.pem;
    
    # SSL security settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-CHACHA20-POLY1305;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    
    # API requests - route to backend
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    # Static files
    location /static/ {
        alias /static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Frontend files
    location / {
        root /frontend;
        try_files \$uri \$uri/ /index.html;
        
        # Security headers for frontend
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        add_header Pragma "no-cache";
        add_header Expires "0";
    }

    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF
        
        echo "Nginx configuration updated! Restarting nginx service..."
        docker-compose -f docker-compose.prod.yml restart nginx
        
        echo "SSL setup completed successfully!"
        echo "Your site should now be accessible via HTTPS at https://$DOMAIN"
    else
        echo "Failed to obtain certificates"
        exit 1
    fi
else
    echo "Dry run failed. Please check your configuration."
    exit 1
fi
