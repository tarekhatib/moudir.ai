#!/bin/sh
set -e

# Apply pending database migrations before serving traffic.
alembic upgrade head

# The API is only reachable through the web proxy on the private network, so trust its
# X-Forwarded-* headers (client IPs are used for sign-in rate limiting).
exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --proxy-headers \
  --forwarded-allow-ips="*" \
  --workers "${WEB_CONCURRENCY:-2}"
