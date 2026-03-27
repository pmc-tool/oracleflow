#!/usr/bin/env bash
set -euo pipefail
BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
echo "Backing up Postgres..."
docker exec oracleflow-postgres pg_dump -U oracleflow oracleflow > "$BACKUP_DIR/postgres.sql"
echo "Backing up Neo4j..."
docker exec oracleflow-neo4j neo4j-admin database dump neo4j --to-path=/tmp/neo4j-backup 2>/dev/null || echo "Neo4j backup skipped"
echo "Backup saved to $BACKUP_DIR"
