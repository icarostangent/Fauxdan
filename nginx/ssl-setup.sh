#!/bin/sh

# Function to check if certificates exist
check_certificates() {
    if [ -f "/etc/letsencrypt/live/fauxdan.io/fullchain.pem" ] && [ -f "/etc/letsencrypt/live/fauxdan.io/privkey.pem" ]; then
        return 0
    else
        return 1
    fi
}

# Function to obtain initial certificates
obtain_certificates() {
    echo "Obtaining Let's Encrypt certificates..."
    
    # Get email from environment variable
    EMAIL=${LETSENCRYPT_EMAIL}
    echo "Using email: $EMAIL"
    
    # Stop nginx temporarily
    nginx -s quit 2>/dev/null || true
    
    # Wait for nginx to stop
    sleep 2
    
    # Obtain certificates
    echo "Obtaining staging certificates..."
    certbot certonly \
        --webroot \
        --webroot-path=/var/www/certbot \
        --email "$EMAIL" \
        --agree-tos \
        --no-eff-email \
        --domains fauxdan.io \
        --non-interactive \
        --staging
    
    # If staging was successful, get production certificates
    if [ $? -eq 0 ]; then
        echo "Staging certificates obtained successfully. Getting production certificates..."
        certbot certonly \
            --webroot \
            --webroot-path=/var/www/certbot \
            --email "$EMAIL" \
            --agree-tos \
            --no-eff-email \
            --domains fauxdan.io \
            --non-interactive
    else
        echo "Failed to obtain staging certificates. Exiting."
        exit 1
    fi
}

# Function to renew certificates
renew_certificates() {
    echo "Renewing Let's Encrypt certificates..."
    certbot renew --quiet
    nginx -s reload
}

# Main execution
echo "Starting SSL setup..."

# Check if we need to obtain initial certificates
if ! check_certificates; then
    echo "No certificates found. Obtaining initial certificates..."
    obtain_certificates
fi

# Start nginx in background
echo "Starting Nginx..."
nginx -g "daemon off;" &
NGINX_PID=$!

# Set up certificate renewal cron job
echo "Setting up certificate renewal..."
echo "0 12 * * * /usr/local/bin/certbot renew --quiet && nginx -s reload" | crontab -

# Wait for nginx to start
sleep 3

# Check if nginx is running
if ! kill -0 $NGINX_PID 2>/dev/null; then
    echo "Failed to start Nginx. Exiting."
    exit 1
fi

echo "Nginx started successfully with PID $NGINX_PID"

# Wait for nginx process
wait $NGINX_PID
