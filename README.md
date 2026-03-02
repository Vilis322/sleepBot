# Sleep Bot

Telegram bot for sleep tracking with multi-language support.

**Try it:** [@sleep_tracks_bot](https://t.me/sleep_tracks_bot)

## Features

- Sleep tracking with `/sleep` and `/wake` commands
- Quality rating (1-10) and notes for each session
- Personal sleep goals with progress tracking
- Statistics export (CSV / JSON)
- Timezone auto-detection via geolocation
- Multi-language interface (English, Russian, Estonian)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Bot framework | aiogram 3.x (async) |
| Database | PostgreSQL 15 + SQLAlchemy 2.0 (async) |
| Migrations | Alembic |
| Validation | Pydantic 2.x |
| Logging | structlog |
| Timezone detection | timezonefinder |
| Testing | pytest + pytest-asyncio |
| CI/CD | GitHub Actions |
| Deployment | Docker + Docker Compose |

## Architecture

```
main.py                     # Entry point, dispatcher setup
config.py                   # Pydantic settings from env
database.py                 # Async engine & session factory

bot/
  handlers/                 # Telegram command & message handlers
    start.py                #   /start + language selection
    onboarding.py           #   Onboarding FSM (bedtime, waketime, goals, timezone)
    sleep.py, wake.py       #   /sleep, /wake — session lifecycle
    quality.py, note.py     #   /quality, /note — session metadata
    stats.py                #   /stats — export flow
    help.py, language.py    #   /help, /language
  keyboards/                # Inline & reply keyboards
  states/                   # FSM state groups
  middlewares/              # Localization middleware (injects lang & loc)

services/                   # Business logic
  user_service.py           #   User CRUD, onboarding, goals
  sleep_service.py          #   Session start/stop, quality, notes
  statistics_service.py     #   Aggregation & export preparation

repositories/               # Data access (SQLAlchemy queries)
  user_repository.py
  sleep_repository.py

models/                     # SQLAlchemy ORM models
  user.py                   #   User, timezone, goals, onboarding status
  sleep_session.py          #   Sleep session with timestamps, quality, notes

localization/               # i18n service + JSON translations (en, ru, et)
utils/                      # Logger, CSV/JSON exporters
```

Layers follow a strict dependency direction: `handlers -> services -> repositories -> models`.

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Initialize bot, configure language, sleep goals, and timezone |
| `/help` | Show available commands |
| `/language` | Change interface language |
| `/sleep` | Start sleep tracking |
| `/wake` | Stop tracking and view session summary |
| `/quality` | Rate sleep quality (1-10) |
| `/note` | Add notes about your sleep |
| `/stats` | View and export sleep statistics |

## Local Development

### Quick start (Make)

```bash
cp .env.example .env       # Fill in BOT_TOKEN and DB credentials
make setup                 # Install deps, start PostgreSQL, run migrations
make run                   # Start the bot
```

### Manual setup

```bash
cp .env.example .env
pip install -e ".[dev]"
docker-compose up -d       # Start PostgreSQL
alembic upgrade head       # Run migrations
python main.py             # Start the bot
```

### Useful Make commands

```
make test          Run all tests with coverage
make test-unit     Run unit tests only
make format        Format code with black
make lint          Run flake8
make db-up         Start PostgreSQL container
make db-down       Stop PostgreSQL container
make clean         Clean generated files
```

## Testing

```bash
make test
# or
pytest --cov=. --cov-report=term-missing
```

Tests use an in-memory SQLite database (via aiosqlite) — no running PostgreSQL required.

## Deployment

Automatically deploys via GitHub Actions on push to `main`:

1. Run tests in CI
2. SSH into server
3. `git fetch && git reset --hard origin/main`
4. Rebuild and restart Docker containers
5. Alembic migrations run on container startup

See [DEPLOYMENT.md](DEPLOYMENT.md) for server setup details.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `BOT_TOKEN` | Telegram Bot API token |
| `DB_HOST` | PostgreSQL host |
| `DB_PORT` | PostgreSQL port (default: 5432) |
| `DB_NAME` | Database name |
| `DB_USER` | Database user |
| `DB_PASSWORD` | Database password |
| `ENVIRONMENT` | `development` or `production` |
| `LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
