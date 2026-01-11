.PHONY: help install install-dev db-up db-down db-init db-migrate db-upgrade run test test-unit test-integration test-smoke coverage clean format lint

help:  ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install production dependencies
	pip install -e .

install-dev:  ## Install all dependencies including dev tools
	pip install -e ".[dev]"

db-up:  ## Start PostgreSQL container
	docker-compose up -d

db-down:  ## Stop PostgreSQL container
	docker-compose down

db-init:  ## Initialize database (create tables)
	alembic upgrade head

db-migrate:  ## Create new migration (use: make db-migrate msg="your message")
	alembic revision --autogenerate -m "$(msg)"

db-upgrade:  ## Apply all pending migrations
	alembic upgrade head

db-downgrade:  ## Rollback last migration
	alembic downgrade -1

run:  ## Run the bot
	python main.py

dev:  ## Run bot in development mode with auto-reload
	python main.py

test:  ## Run all tests with coverage
	pytest --cov=. --cov-report=term-missing --cov-report=html

test-unit:  ## Run only unit tests
	pytest tests/unit/ -v

test-integration:  ## Run only integration tests
	pytest tests/integration/ -v

test-smoke:  ## Run only smoke tests
	pytest tests/smoke/ -v

coverage:  ## Generate and open HTML coverage report
	pytest --cov=. --cov-report=html
	@echo "Opening coverage report..."
	@open htmlcov/index.html || xdg-open htmlcov/index.html

format:  ## Format code with black
	black .

lint:  ## Run linters (flake8, mypy)
	flake8 . --exclude=venv,alembic
	mypy . --exclude=venv --exclude=alembic

clean:  ## Clean up generated files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov .coverage coverage.xml
	@echo "Cleaned up generated files"

setup:  ## Complete local setup (install deps, start db, run migrations)
	@echo "📦 Installing dependencies..."
	make install-dev
	@echo "🐘 Starting PostgreSQL..."
	make db-up
	@echo "⏳ Waiting for database to be ready..."
	sleep 3
	@echo "🗄️  Running migrations..."
	make db-init
	@echo "✅ Setup complete! Copy .env.example to .env and fill in your credentials"
	@echo "Then run: make run"

setup-quick: install-dev db-up db-init  ## Quick setup (all in one command)

logs:  ## Show docker-compose logs
	docker-compose logs -f

ps:  ## Show running containers
	docker-compose ps
