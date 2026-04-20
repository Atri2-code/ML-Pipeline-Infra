#!/usr/bin/env bash
# healthcheck.sh — post-deploy liveness probe loop
# Polls /healthz and /ready until the service is confirmed healthy
# or the timeout is exceeded.
# Usage: ./scripts/healthcheck.sh [host] [max_retries] [interval]

set -euo pipefail

HOST="${1:-localhost}"
PORT="${2:-8080}"
MAX_RETRIES="${3:-20}"
INTERVAL="${4:-5}"

HEALTHZ_URL="http://${HOST}:${PORT}/healthz"
READY_URL="http://${HOST}:${PORT}/ready"

echo "==> Starting post-deploy healthcheck"
echo "    target : ${HOST}:${PORT}"
echo "    retries: ${MAX_RETRIES} x ${INTERVAL}s"

attempt=0

until curl -sf "${HEALTHZ_URL}" > /dev/null 2>&1; do
  attempt=$((attempt + 1))
  if [[ ${attempt} -ge ${MAX_RETRIES} ]]; then
    echo "ERROR: /healthz did not respond after ${MAX_RETRIES} attempts"
    exit 1
  fi
  echo "  [${attempt}/${MAX_RETRIES}] waiting for /healthz ..."
  sleep "${INTERVAL}"
done

echo "==> /healthz OK — checking /ready"

attempt=0

until curl -sf "${READY_URL}" > /dev/null 2>&1; do
  attempt=$((attempt + 1))
  if [[ ${attempt} -ge ${MAX_RETRIES} ]]; then
    echo "ERROR: /ready did not respond after ${MAX_RETRIES} attempts"
    exit 1
  fi
  echo "  [${attempt}/${MAX_RETRIES}] waiting for /ready (model loading) ..."
  sleep "${INTERVAL}"
done

echo "==> Service is live and ready"
exit 0
