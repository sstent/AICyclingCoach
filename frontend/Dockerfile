# Stage 1: Build application
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package manifests first for optimal caching
COPY package.json package-lock.json* ./

# Clean cache and install dependencies
RUN npm cache clean --force && \
    export NODE_OPTIONS="--max-old-space-size=1024" && \
    npm install --include=dev

# Copy source files
COPY . .

# Build application with production settings
RUN export NODE_OPTIONS="--max-old-space-size=1024" && \
    npm run build

# Stage 2: Production runtime
FROM nginx:1.25-alpine

# Install curl for healthchecks
RUN apk add --no-cache curl

# Create necessary directories and set permissions
RUN mkdir -p /var/cache/nginx/client_temp && \
    mkdir -p /var/run/nginx && \
    chown -R nginx:nginx /usr/share/nginx/html && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/run/nginx && \
    chmod -R 755 /usr/share/nginx/html

# Copy build artifacts
COPY --from=builder /app/.next /usr/share/nginx/html/_next

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Copy Next.js routes manifest for proper routing
COPY --from=builder /app/.next/routes-manifest.json /usr/share/nginx/html/_next/

# Copy main HTML files to root
COPY --from=builder /app/.next/server/pages/index.html /usr/share/nginx/html/index.html
COPY --from=builder /app/.next/server/pages/404.html /usr/share/nginx/html/404.html

# Modify nginx config to use custom PID path
RUN sed -i 's|pid        /var/run/nginx.pid;|pid        /var/run/nginx/nginx.pid;|' /etc/nginx/nginx.conf

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:80 || exit 1

# Run as root to avoid permission issues
# USER nginx

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]