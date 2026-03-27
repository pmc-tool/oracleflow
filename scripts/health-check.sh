#!/usr/bin/env bash
echo "=== OracleFlow Health Check ==="
echo "Nginx:    $(curl -s -o /dev/null -w '%{http_code}' http://localhost/ || echo 'DOWN')"
echo "API:      $(curl -s -o /dev/null -w '%{http_code}' http://localhost/api/health || echo 'DOWN')"
echo "Neo4j:    $(curl -s -o /dev/null -w '%{http_code}' http://localhost:7474 || echo 'DOWN')"
echo "Postgres: $(docker exec oracleflow-postgres pg_isready -U oracleflow 2>&1 | tail -1)"
echo "Redis:    $(docker exec oracleflow-redis redis-cli ping 2>&1)"
