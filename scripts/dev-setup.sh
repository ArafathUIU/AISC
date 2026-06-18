#!/usr/bin/env bash
set -euo pipefail

echo "=== AISC Development Environment Setup ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo ""
echo "[1/5] Copying environment file..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "  Created .env from .env.example"
else
    echo "  .env already exists, skipping"
fi

echo ""
echo "[2/5] Starting infrastructure services..."
docker compose up -d --wait postgres redis kafka zookeeper schema-registry qdrant neo4j

echo ""
echo "[3/5] Waiting for services to be healthy..."
# PostgreSQL
echo "  Waiting for PostgreSQL..."
until docker compose exec -T postgres pg_isready -U aisc -d aisc 2>/dev/null; do
    sleep 2
done
echo "  PostgreSQL is ready"

# Redis
echo "  Waiting for Redis..."
until docker compose exec -T redis redis-cli ping 2>/dev/null | grep -q PONG; do
    sleep 2
done
echo "  Redis is ready"

# Kafka
echo "  Waiting for Kafka..."
until docker compose exec -T kafka kafka-broker-api-versions --bootstrap-server localhost:9092 2>/dev/null; do
    sleep 3
done
echo "  Kafka is ready"

# Qdrant
echo "  Waiting for Qdrant..."
until curl -sf http://localhost:6333/healthz 2>/dev/null; do
    sleep 2
done
echo "  Qdrant is ready"

# Neo4j
echo "  Waiting for Neo4j..."
until curl -sf http://localhost:7474 2>/dev/null; do
    sleep 3
done
echo "  Neo4j is ready"

echo ""
echo "[4/5] Installing Python packages..."
pip install -e libs/aisc-models -e libs/aisc-utils -e libs/aisc-events -e libs/aisc-proto -q

echo ""
echo "[5/5] Running database migrations..."
# Placeholder - will run Alembic migrations when services are built
echo "  No migrations to run yet (services not yet implemented)"

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Services running:"
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
echo ""
echo "Use 'docker compose down' to stop all services."
echo "Use 'make help' to see available commands."
