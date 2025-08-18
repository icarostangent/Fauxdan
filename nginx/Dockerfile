FROM nginx:latest

# Install necessary packages
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create necessary directories
RUN mkdir -p /static /frontend /var/log/nginx

# Copy nginx configuration
COPY nginx/conf/ /etc/nginx/conf.d/

# Copy static files (if any)
COPY static/ /static/

# Copy frontend files (if any)
COPY frontend/ /frontend/

# Set proper permissions
RUN chown -R nginx:nginx /static /frontend /var/log/nginx

# Expose ports
EXPOSE 80 443

# Start nginx
CMD ["nginx", "-g", "daemon off;"]