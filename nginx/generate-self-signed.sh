#!/bin/sh

# Generate self-signed certificate for development
echo "Generating self-signed certificate for development..."

# Create SSL directory if it doesn't exist
mkdir -p /etc/nginx/ssl

# Generate private key
openssl genrsa -out /etc/nginx/ssl/key.pem 2048

# Generate certificate signing request and self-signed certificate
openssl req -new -x509 -key /etc/nginx/ssl/key.pem -out /etc/nginx/ssl/cert.pem -days 365 -subj "/C=US/ST=State/L=City/O=Fauxdan/CN=localhost"

# Set proper permissions
chown -R nginx:nginx /etc/nginx/ssl
chmod 600 /etc/nginx/ssl/key.pem
chmod 644 /etc/nginx/ssl/cert.pem

echo "Self-signed certificate generated successfully!"
echo "Certificate: /etc/nginx/ssl/cert.pem"
echo "Private key: /etc/nginx/ssl/key.pem"
