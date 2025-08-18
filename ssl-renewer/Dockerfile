FROM alpine:latest

# Install required packages
RUN apk add --no-cache \
    dcron \
    docker-cli \
    curl \
    bash \
    jq

# Create renewal script directory
RUN mkdir -p /usr/local/bin

# Copy renewal script
COPY renew-ssl.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/renew-ssl.sh

# Create cron directory
RUN mkdir -p /etc/crontabs

# Create entrypoint script
COPY entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh

# Expose port for health checks (optional)
EXPOSE 8080

# Set entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
