.PHONY: help dev-setup start stop clean lint typecheck test build docker-build docker-up docker-down

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ============ Development ============

dev-setup: ## Initialize development environment (start infra, run migrations)
	@bash scripts/dev-setup.sh

start: ## Start all services locally (without Docker)
	@echo "Starting AISC services..."

stop: ## Stop all locally running services
	@echo "Stopping AISC services..."

clean: ## Clean build artifacts and caches
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf dist/ build/

# ============ Quality ============

lint: ## Run ruff linter
	@ruff check services/ libs/

format: ## Run ruff formatter
	@ruff format services/ libs/

typecheck: ## Run mypy type checker
	@mypy services/ libs/ || echo "No Python files to check yet."

test: ## Run all tests
	@pytest services/ libs/ -v

test-cov: ## Run tests with coverage
	@pytest services/ libs/ -v --cov --cov-report=term --cov-report=html

# ============ Docker ============

docker-build: ## Build all service Docker images
	@echo "Building Docker images..."
	@for service in auth-service orchestrator-service agent-runtime quality-gate-service scoring-engine rag-service memory-service self-learning-service self-healing-service debate-service observability-service ws-gateway; do \
		docker build -t aisc/$$service:latest -f services/$$service/Dockerfile . ; \
	done

docker-up: ## Start all services via docker-compose
	@docker compose up -d

docker-down: ## Stop all services via docker-compose
	@docker compose down

docker-logs: ## Tail logs from all containers
	@docker compose logs -f

# ============ Database ============

db-migrate: ## Run database migrations
	@echo "Running database migrations..."

db-seed: ## Seed database with test data
	@bash scripts/seed-data.sh

# ============ Monitoring ============

prometheus: ## Start Prometheus
	@docker compose up -d prometheus

grafana: ## Start Grafana
	@docker compose up -d grafana

# ============ CI ============

ci: lint typecheck test ## Run full CI pipeline locally
