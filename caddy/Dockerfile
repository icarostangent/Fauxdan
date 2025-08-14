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

# Final Caddy stage
FROM caddy:2-alpine

# Copy the built frontend files
COPY --from=frontend-builder /app/dist /frontend

# Copy Caddy configuration
COPY caddy/Caddyfile /etc/caddy/Caddyfile

EXPOSE 80 443
