# =============================================================================
# Production Frontend Dockerfile
# Multi-stage build: Node build + Nginx serve
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Build
# -----------------------------------------------------------------------------
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY frontend/package.json frontend/package-lock.json* ./

# Install dependencies
RUN npm ci --only=production=false

# Copy source code
COPY frontend/ ./

# Build the application
# Note: VITE_API_URL should be set during build time for production
ARG VITE_API_URL=/api/v1
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# -----------------------------------------------------------------------------
# Stage 2: Production - Nginx
# -----------------------------------------------------------------------------
FROM nginx:1.25-alpine AS production

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom nginx config
COPY frontend/nginx.conf /etc/nginx/nginx.conf

# Copy built static files
COPY --from=builder /app/dist /usr/share/nginx/html

# Create nginx user if needed and set permissions
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    chown -R nginx:nginx /etc/nginx/conf.d && \
    touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]