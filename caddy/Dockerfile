# Build stage for frontend
FROM node:22-alpine AS frontend-builder
WORKDIR /app

# Build with a placeholder that will be replaced at runtime
ENV VUE_APP_API_URL=__RUNTIME_API_URL__

# Copy package files and install ALL dependencies
COPY frontend/package*.json ./
RUN npm ci 

# Copy frontend source code
COPY frontend/ ./

# Build the Vue application with placeholder
RUN npm run build

# Create a script to replace the placeholder at runtime
RUN echo '#!/bin/sh\n\
sed -i "s|__RUNTIME_API_URL__|$VUE_APP_API_URL|g" /frontend/index.html\n\
sed -i "s|__RUNTIME_API_URL__|$VUE_APP_API_URL|g" /frontend/assets/*.js\n\
exec caddy run --config /etc/caddy/Caddyfile --adapter caddyfile' > /start.sh && chmod +x /start.sh

# Final Caddy stage
FROM caddy:2-alpine

# Copy the built frontend files
COPY --from=frontend-builder /app/dist /frontend

# Copy the runtime configuration script
COPY --from=frontend-builder /start.sh /start.sh

# Copy Caddy configuration
COPY caddy/Caddyfile /etc/caddy/Caddyfile

# Set the entrypoint to our runtime script
ENTRYPOINT ["/start.sh"]

EXPOSE 80 443
