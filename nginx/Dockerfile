# Build stage for frontend

FROM node:22-alpine AS frontend-builder
WORKDIR /app

# Accept build argument
ARG VUE_APP_API_URL
ENV VUE_APP_API_URL=$VUE_APP_API_URL

# Copy package files and install ALL dependencies
COPY frontend/package*.json ./
RUN npm ci 

# Copy frontend source code
COPY frontend/ ./

# Build the Vue application (now with environment variable available)
RUN npm run build

# Final Nginx stage
FROM nginx:alpine

# Install additional tools for SSL certificate generation and Let's Encrypt
RUN apk add --no-cache openssl certbot

# Create necessary directories
RUN mkdir -p /etc/nginx/ssl /var/www/certbot /etc/letsencrypt

# Copy the built frontend files
COPY --from=frontend-builder /app/dist /frontend

# Copy Nginx configuration
COPY nginx/nginx.conf /etc/nginx/nginx.conf

# Copy SSL setup script
COPY nginx/ssl-setup.sh /usr/local/bin/ssl-setup.sh
RUN chmod +x /usr/local/bin/ssl-setup.sh

# Set proper permissions
RUN chown -R nginx:nginx /frontend /var/cache/nginx /var/log/nginx /etc/letsencrypt /var/www/certbot
RUN chmod -R 755 /frontend /var/cache/nginx /var/log/nginx /etc/letsencrypt /var/www/certbot

EXPOSE 80 443

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/health || exit 1

# Use the SSL setup script as entrypoint
ENTRYPOINT ["/usr/local/bin/ssl-setup.sh"]