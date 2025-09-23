.PHONY: help venv install install-dev test dev dev-redis redis-start redis-stop run down clean clean-all

# Virtual environment path
VENV_PATH = .venv
PYTHON = $(VENV_PATH)/bin/python
PIP = $(VENV_PATH)/bin/pip
PYTEST = $(VENV_PATH)/bin/pytest

# Default target
help: ## Print available targets and their descriptions
	@echo "🚀 Chat API - Development Commands"
	@echo ""
	@echo "Quick Start:"
	@echo "  make install     # Install dependencies"
	@echo "  make run         # Start full stack (RECOMMENDED)"
	@echo "  make test        # Run tests"
	@echo "  make clean       # Clean up everything"
	@echo ""
	@echo "All Commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'
	@echo ""
	@echo "Development Workflow:"
	@echo "  1. make install      # Set up everything (venv + dependencies + Docker images)"
	@echo "  2. make dev          # Run API locally (in-memory storage)"
	@echo "  3. make dev-redis    # Run API locally with Redis"
	@echo "  4. make test         # Run tests"
	@echo "  5. make run          # Run full stack with Docker"

# Virtual environment management
venv: ## Create Python virtual environment
	@echo "Creating virtual environment..."
	@if [ ! -d "$(VENV_PATH)" ]; then \
		python3 -m venv $(VENV_PATH); \
		echo "✅ Virtual environment created at $(VENV_PATH)"; \
	else \
		echo "✅ Virtual environment already exists at $(VENV_PATH)"; \
	fi
	@if [ ! -f "$(PIP)" ]; then \
		echo "❌ Virtual environment pip not found at $(PIP)"; \
		echo "Try: rm -rf $(VENV_PATH) && make venv"; \
		exit 1; \
	fi

install: venv ## Install all dependencies (Python + Docker images)
	@echo "Installing Python dependencies in virtual environment..."
	@echo "Using pip at: $(PIP)"
	@$(PIP) --version
	@$(PIP) install --upgrade pip
	@$(PIP) install -r requirements.txt
	@echo "Checking for Docker..."
	@docker --version >/dev/null 2>&1 || (echo "❌ Docker not found! Please install Docker." && exit 1)
	@echo "Checking for Docker Compose..."
	@docker compose version >/dev/null 2>&1 || (echo "❌ Docker Compose not found! Please install Docker Compose." && exit 1)
	@echo "Pulling Docker images..."
	@docker pull redis:7-alpine >/dev/null 2>&1 || echo "⚠️  Could not pull Redis image (Docker daemon may not be running)"
	@echo "✅ Installation complete!"
	@echo ""
	@echo "Python environment info:"
	@echo "  Virtual env: $(VENV_PATH)"
	@echo "  Python: $(PYTHON)"
	@echo "  Pip: $(PIP)"
	@$(PYTHON) --version
	@$(PIP) list | head -10
	@echo ""
	@echo "Next steps:"
	@echo "  - Run 'make dev' for local development"
	@echo "  - Run 'make test' to run tests"
	@echo "  - Run 'make run' for full Docker stack"

install-dev: venv ## Install development dependencies only (no Docker)
	@echo "Installing development dependencies in virtual environment..."
	@echo "Using pip at: $(PIP)"
	@$(PIP) install --upgrade pip
	@$(PIP) install -r requirements.txt
	@echo "✅ Development setup complete!"

# Testing
test: venv ## Run tests with pytest in virtual environment
	@echo "Running tests in virtual environment..."
	@echo "Using Python: $(PYTHON)"
	@echo "Using pytest: $(PYTEST)"
	@cd . && PYTHONPATH=. $(PYTEST) -q

test-verbose: venv ## Run tests with verbose output
	@echo "Running tests with verbose output..."
	@echo "Using Python: $(PYTHON)"
	@echo "Using pytest: $(PYTEST)"
	@cd . && PYTHONPATH=. $(PYTEST) -v

verify-env: venv ## Verify virtual environment is working correctly
	@echo "🔍 Virtual Environment Verification"
	@echo "=================================="
	@echo "Virtual env path: $(VENV_PATH)"
	@echo "Python path: $(PYTHON)"
	@echo "Pip path: $(PIP)"
	@echo "Pytest path: $(PYTEST)"
	@echo ""
	@echo "🐍 Python version:"
	@$(PYTHON) --version
	@echo ""
	@echo "📦 Python location:"
	@$(PYTHON) -c "import sys; print(f'Executable: {sys.executable}'); print(f'Prefix: {sys.prefix}')"
	@echo ""
	@echo "📚 Installed packages (first 15):"
	@$(PIP) list | head -15
	@echo ""
	@echo "✅ Virtual environment verification complete!"

# Local development
dev: venv ## Run API locally using virtual environment (in-memory storage)
	@echo "Starting API locally (in-memory storage)..."
	@echo "🚀 API will be available at http://localhost:8000"
	@echo "📚 API docs at http://localhost:8000/docs"
	@echo "🔍 Health check at http://localhost:8000/healthz"
	@echo ""
	@cd . && PYTHONPATH=. $(PYTHON) -m api.main

dev-redis: redis-start venv ## Run API locally with Redis backend
	@echo "Starting API locally with Redis backend..."
	@echo "🚀 API will be available at http://localhost:8000"
	@echo "📚 API docs at http://localhost:8000/docs"
	@echo "🗄️  Redis backend at localhost:6379"
	@echo ""
	@cd . && PYTHONPATH=. REDIS_URL=redis://localhost:6379 $(PYTHON) -m api.main

# Redis management
redis-start: ## Start Redis in Docker for local development
	@echo "Starting Redis for local development..."
	@docker run -d --name chat-api-redis -p 6379:6379 redis:7-alpine >/dev/null 2>&1 || \
		(docker start chat-api-redis >/dev/null 2>&1 && echo "♻️  Redis container already exists, started it") || \
		echo "❌ Failed to start Redis"
	@echo "✅ Redis running at localhost:6379"

redis-stop: ## Stop Redis Docker container
	@echo "Stopping Redis container..."
	@docker stop chat-api-redis >/dev/null 2>&1 || echo "Redis container not running"
	@echo "✅ Redis stopped"

redis-clean: ## Stop and remove Redis container
	@echo "Cleaning up Redis container..."
	@docker stop chat-api-redis >/dev/null 2>&1 || echo "Redis container not running"
	@docker rm chat-api-redis >/dev/null 2>&1 || echo "Redis container not found"
	@echo "✅ Redis container cleaned up"

# Docker deployment
run: ## Build and run API with in-memory storage (default)
	@echo "Building and starting API with in-memory storage..."
	@echo "🚀 API will be available at http://localhost:8000"
	@echo "📝 Using in-memory conversation storage"
	@docker compose up --build

run-redis: ## Build and run API with Redis storage
	@echo "Building and starting API with Redis storage..."
	@echo "🚀 API will be available at http://localhost:8000"
	@echo "🗄️  Redis will be available at localhost:6379"
	@docker compose --profile redis up --build

run-detached: ## Run API in background with in-memory storage
	@echo "Starting API in detached mode with in-memory storage..."
	@docker compose up --build -d
	@echo "✅ API running in background with in-memory storage"
	@echo "View logs: make logs"
	@echo "Stop services: make down"

logs: ## View Docker Compose logs
	@docker compose logs -f

down: ## Stop Docker Compose services
	@echo "Stopping services..."
	@docker compose down
	@echo "✅ Services stopped"

# Cleanup targets
clean: ## Clean up Docker resources
	@echo "Cleaning up Docker resources..."
	@docker compose down -v --remove-orphans >/dev/null 2>&1 || echo "No compose services to stop"
	@docker system prune -f >/dev/null 2>&1 || echo "Docker cleanup completed"
	@echo "✅ Docker cleanup complete"

clean-all: clean redis-clean ## Complete cleanup (Docker + Redis + virtual environment)
	@echo "Performing complete cleanup..."
	@rm -rf $(VENV_PATH) 2>/dev/null || echo "No virtual environment to remove"
	@rm -rf .pytest_cache __pycache__ api/__pycache__ api/tests/__pycache__ 2>/dev/null || true
	@docker rmi chat-api:latest >/dev/null 2>&1 || echo "No chat-api image to remove"
	@echo "✅ Complete cleanup finished"

# Development utilities
lint: venv ## Run code linting with ruff
	@echo "Running linter in virtual environment..."
	@echo "Using Python: $(PYTHON)"
	@$(PYTHON) -m ruff check api/

lint-fix: venv ## Fix linting issues automatically
	@echo "Fixing linting issues in virtual environment..."
	@echo "Using Python: $(PYTHON)"
	@$(PYTHON) -m ruff check api/ --fix
	@$(PYTHON) -m ruff format api/

check: test lint ## Run all checks (tests + linting)
	@echo "✅ All checks passed!"
