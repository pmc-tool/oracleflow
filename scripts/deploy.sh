#!/usr/bin/env bash
set -euo pipefail
echo "=== OracleFlow Deploy ==="
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
echo "Waiting for services..."
sleep 10
docker compose -f docker-compose.prod.yml ps
echo "=== Deploy complete ==="
