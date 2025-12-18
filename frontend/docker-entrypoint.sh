#!/bin/sh
set -e

# Default API URL if not set
API_URL=${API_URL:-http://backend:8000}

# Replace environment variables in nginx config
envsubst '${API_URL}' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf

# Start nginx
exec nginx -g 'daemon off;'