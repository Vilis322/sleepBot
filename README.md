# Sleep Bot

Telegram bot for sleep tracking with multi-language support (English, Russian, Estonian).

## Features

- 🌍 Multi-language support (EN, RU, ET)
- 😴 Sleep tracking with start/wake commands
- 📊 Quality rating and notes for each sleep session
- 📈 Statistics export (CSV/JSON)
- ⏰ Timezone-aware tracking
- 🎯 Personal sleep goals and insights

## Tech Stack

- **Framework**: aiogram 3.x
- **Database**: PostgreSQL + SQLAlchemy (async)
- **Logging**: structlog
- **Testing**: pytest with 95%+ coverage
- **CI/CD**: GitHub Actions
- **Deployment**: Docker + Docker Compose

## Local Development

### Option 1: Using Make commands (Recommended)

1. Clone the repository
2. Copy `.env.example` to `.env` and fill in your credentials
3. Run complete setup:
   ```bash
   make setup
   ```
   This will:
   - Install all dependencies
   - Start PostgreSQL container
   - Run database migrations
   
4. Start the bot:
   ```bash
   make run
   ```

### Option 2: Manual setup

1. Clone the repository
2. Copy `.env.example` to `.env` and fill in your credentials
3. Install dependencies:
   ```bash
   pip install -e ".[dev]"
   ```
4. Start PostgreSQL:
   ```bash
   docker-compose up -d
   ```
5. Run migrations:
   ```bash
   alembic upgrade head
   ```
6. Start the bot:
   ```bash
   python main.py
   ```

## Available Make Commands

Run `make help` to see all available commands:

```bash
make help          # Show all available commands
make install       # Install production dependencies
make install-dev   # Install all dependencies including dev tools
make db-up         # Start PostgreSQL container
make db-down       # Stop PostgreSQL container
make db-init       # Initialize database (create tables)
make db-migrate    # Create new migration
make run           # Run the bot
make test          # Run all tests with coverage
make test-unit     # Run only unit tests
make format        # Format code with black
make lint          # Run linters
make clean         # Clean up generated files
make setup         # Complete local setup (recommended for first time)
```

## Testing

```bash
# Run all tests with coverage
make test

# Or manually:
pytest --cov=. --cov-report=term-missing --cov-report=html

# Run specific test types
make test-unit          # Unit tests
make test-integration   # Integration tests
make test-smoke         # Smoke tests
```

## Deployment

The bot uses Docker for production deployment. See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

**Quick Deploy:**
- Automatically deploys via GitHub Actions on push to `main` branch
- Uses Docker Compose for container orchestration
- PostgreSQL data persisted in Docker volumes

## Architecture

The project follows SOLID principles with clear separation of concerns:

- `bot/` - Telegram bot handlers, keyboards, and FSM states
- `services/` - Business logic layer
- `repositories/` - Database access layer
- `models/` - SQLAlchemy database models
- `schemas/` - Pydantic validation schemas
- `localization/` - Multi-language support
- `utils/` - Helper functions and exporters

## Commands

- `/start` - Initialize bot and set preferences
- `/help` - Show available commands
- `/language` - Change interface language
- `/sleep` - Start sleep tracking
- `/wake` - Stop tracking and view statistics
- `/quality <rating>` - Rate sleep quality (1-10)
- `/note <text>` - Add notes about sleep
- `/stats` - Export sleep statistics

## Database Setup

The bot requires PostgreSQL. You can either:
1. Use Docker Compose (recommended): `make db-up`
2. Use existing PostgreSQL server (update `.env` with connection details)

To create a separate database on existing PostgreSQL:
```sql
CREATE DATABASE sleepbot_db;
CREATE USER sleepbot_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE sleepbot_db TO sleepbot_user;
```
