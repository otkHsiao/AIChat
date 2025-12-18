# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build arguments for environment variables
ARG VITE_API_BASE_URL=/api

# Set environment variables for build
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

# Build the app
RUN npm run build

# Production stage
FROM nginx:alpine

# Install envsubst for template processing
RUN apk add --no-cache gettext

# Copy nginx config template
COPY nginx.conf.template /etc/nginx/conf.d/default.conf.template

# Copy entrypoint script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Default environment variable
ENV API_URL=http://backend:8000

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost/health || exit 1

# Use custom entrypoint
ENTRYPOINT ["/docker-entrypoint.sh"]