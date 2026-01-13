.PHONY: help venv venv-install venv-remove venv-status db-up db-down db-clean db-migrate db-upgrade db-downgrade db-current db-history db-reset run test coverage mock unit integration smoke cover format lint clean setup-venv logs ps

help:  ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

venv:  ## Create virtual environment (checks if exists)
	@if [ -d ".venv" ]; then \
		echo "✅ Virtual environment already exists at .venv"; \
		if [ -n "$$VIRTUAL_ENV" ]; then \
			echo "✅ Virtual environment is ACTIVATED"; \
		else \
			echo "⚠️  Virtual environment is NOT activated"; \
			echo "Run: source .venv/bin/activate"; \
		fi; \
	else \
		echo "🔧 Creating virtual environment..."; \
		python3 -m venv .venv; \
		echo ""; \
		echo "✅ Virtual environment created at .venv"; \
		echo ""; \
		echo "📝 Next steps:"; \
		echo "   1. Activate: source .venv/bin/activate"; \
		echo "   2. Install: make venv-install"; \
		echo ""; \
		echo "💡 Tip: Add this alias to your ~/.zshrc or ~/.bashrc:"; \
		echo "   alias venv='source .venv/bin/activate'"; \
	fi

venv-status:  ## Check virtual environment status
	@echo "🔍 Virtual environment status:"
	@if [ -d ".venv" ]; then \
		echo "   ✅ .venv directory exists"; \
		if [ -n "$$VIRTUAL_ENV" ]; then \
			echo "   ✅ Virtual environment is ACTIVATED"; \
			echo "   📍 Location: $$VIRTUAL_ENV"; \
			echo "   🐍 Python: $$(python --version)"; \
			echo "   📦 Pip: $$(pip --version)"; \
		else \
			echo "   ⚠️  Virtual environment is NOT activated"; \
			echo "   💡 Run: source .venv/bin/activate"; \
		fi; \
	else \
		echo "   ❌ .venv directory does not exist"; \
		echo "   💡 Run: make venv"; \
	fi

venv-install:  ## Install dependencies in venv (run after activating venv)
	@if [ -z "$$VIRTUAL_ENV" ]; then \
		echo "❌ Virtual environment not activated!"; \
		echo ""; \
		echo "Please run:"; \
		echo "   source .venv/bin/activate"; \
		echo "   make venv-install"; \
		exit 1; \
	fi
	@echo "📦 Installing dependencies from pyproject.toml..."
	pip install --upgrade pip setuptools wheel
	@echo ""
	@echo "📦 Reading dependencies from pyproject.toml..."
	@python3 -c "import tomllib; f = open('pyproject.toml', 'rb'); data = tomllib.load(f); deps = data['project']['dependencies']; print(' '.join(deps))" | xargs pip install
	@echo ""
	@echo "📦 Installing dev dependencies..."
	@python3 -c "import tomllib; f = open('pyproject.toml', 'rb'); data = tomllib.load(f); deps = data['project']['optional-dependencies']['dev']; print(' '.join(deps))" | xargs pip install
	@echo ""
	@echo "✅ Dependencies installed in venv!"
	@echo "🐍 Python: $$(python --version)"
	@echo "📦 Pip: $$(pip --version)"

venv-remove:  ## Remove virtual environment
	@if [ -n "$$VIRTUAL_ENV" ]; then \
		echo "❌ Cannot remove venv while it's activated!"; \
		echo "First run: deactivate"; \
		exit 1; \
	fi
	@if [ -d ".venv" ]; then \
		echo "🗑️  Removing virtual environment..."; \
		rm -rf .venv; \
		echo "✅ Virtual environment removed"; \
	else \
		echo "ℹ️  No virtual environment found"; \
	fi

db-up:  ## Start PostgreSQL container
	docker-compose up -d

db-down:  ## Stop PostgreSQL container
	docker-compose down

db-clean:  ## Stop and remove PostgreSQL container and volumes (WARNING: deletes all data!)
	@echo "⚠️  WARNING: This will delete ALL database data!"
	@echo "Press Ctrl+C to cancel, or Enter to continue..."
	@read confirm
	docker-compose down -v
	@echo "✅ Database cleaned. Run 'make db-up' to start fresh"

db-migrate:  ## Create new migration (use: make db-migrate msg="your message")
	alembic revision --autogenerate -m "$(msg)"

db-upgrade:  ## Apply all pending migrations (also works for initial setup)
	alembic upgrade head

db-downgrade:  ## Rollback last migration
	alembic downgrade -1

db-current:  ## Show current migration version
	alembic current

db-history:  ## Show migration history
	alembic history --verbose

db-reset:  ## Reset database (WARNING: deletes all data!)
	@echo "⚠️  WARNING: This will delete ALL data in the database!"
	@echo "Press Ctrl+C to cancel, or Enter to continue..."
	@read confirm
	alembic downgrade base
	alembic upgrade head

run:  ## Run the bot
	python3 main.py

test:  ## Run tests (use: make test [mock|unit|integration|smoke|cover], or no flag for all)
	@if [ "$(filter-out $@,$(MAKECMDGOALS))" = "mock" ]; then \
		echo "🧪 Running mock tests..."; \
		pytest tests/mock/ -v; \
	elif [ "$(filter-out $@,$(MAKECMDGOALS))" = "unit" ]; then \
		echo "🧪 Running unit tests..."; \
		pytest tests/unit/ -v; \
	elif [ "$(filter-out $@,$(MAKECMDGOALS))" = "integration" ]; then \
		echo "🧪 Running integration tests..."; \
		pytest tests/integration/ -v; \
	elif [ "$(filter-out $@,$(MAKECMDGOALS))" = "smoke" ]; then \
		echo "🧪 Running smoke tests..."; \
		pytest tests/smoke/ -v; \
	elif [ "$(filter-out $@,$(MAKECMDGOALS))" = "cover" ]; then \
		echo "📊 Running all tests with coverage..."; \
		pytest tests/ --cov=services --cov=repositories --cov=models --cov=bot --cov=utils --cov=localization --cov-report=term-missing --cov-report=html; \
		echo ""; \
		echo "✅ Coverage report generated: htmlcov/index.html"; \
	else \
		echo "🧪 Running all tests..."; \
		pytest tests/ -v; \
	fi

# Allow test flags to work without errors
mock unit integration smoke cover:
	@:

coverage:  ## Generate and open HTML coverage report
	pytest tests/ --cov=services --cov=repositories --cov=models --cov=bot --cov=utils --cov=localization --cov-report=html
	@echo "📊 Opening coverage report..."
	@open htmlcov/index.html 2>/dev/null || xdg-open htmlcov/index.html 2>/dev/null || echo "✅ Coverage report generated: htmlcov/index.html"

format:  ## Format code with black
	black .

lint:  ## Run linters (flake8, mypy)
	flake8 . --exclude=.venv,alembic
	mypy . --exclude=.venv --exclude=alembic

clean:  ## Clean up generated files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov .coverage coverage.xml
	@echo "Cleaned up generated files"

setup-venv:  ## Complete setup with virtual environment (RECOMMENDED)
	@echo "🔧 Creating virtual environment..."
	make venv
	@echo ""
	@echo "⚠️  IMPORTANT: Now run these commands manually:"
	@echo "   1. source .venv/bin/activate"
	@echo "   2. make venv-install"
	@echo "   3. make db-up"
	@echo "   4. sleep 5"
	@echo "   5. make db-migrate msg=\"Initial migration\""
	@echo "   6. make db-upgrade"
	@echo "   7. make run"
	@echo ""
	@echo "Or use the script below (copy-paste):"
	@echo "source .venv/bin/activate && make venv-install && make db-up && sleep 5 && make db-migrate msg=\"Initial migration\" && make db-upgrade"

logs:  ## Show docker-compose logs
	docker-compose logs -f

ps:  ## Show running containers
	docker-compose ps
