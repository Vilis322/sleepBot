# Sleep Bot - Setup Guide

Quick setup guide for local development and production deployment.

## Local Development Setup

### 1. Prerequisites

- Python 3.11+
- PostgreSQL 15+ (or Docker)
- Git

### 2. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/Vilis322/sleepBot.git
cd sleepBot

# Switch to dev branch
git checkout dev/setup

# Copy environment file
cp .env.example .env
```

### 3. Get Telegram Bot Token

1. Open Telegram and find [@BotFather](https://t.me/botfather)
2. Send `/newbot` and follow instructions
3. Copy the bot token
4. Add to `.env`:
   ```
   BOT_TOKEN=your_bot_token_here
   ```

### 4. Start Development Environment

```bash
# Option 1: Using Make (Recommended)
make setup        # Install deps, start DB, run migrations
make run          # Start the bot

# Option 2: Manual
pip install -e ".[dev]"
docker-compose up -d
alembic upgrade head
python main.py
```

### 5. Create Initial Migration

```bash
# Generate initial migration
alembic revision --autogenerate -m "Initial migration"

# Apply migration
alembic upgrade head
```

### 6. Test the Bot

Open Telegram and search for your bot, then:
1. Send `/start` - should show welcome message
2. Select language
3. Complete onboarding
4. Try `/sleep` and `/wake` commands

---

## Production Deployment

### Prerequisites on Server

```bash
# Install Python 3.11
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip

# Install PostgreSQL (if not already installed)
sudo apt install postgresql postgresql-contrib

# Install PM2
npm install -g pm2
```

### 1. Create Database

```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Create database and user
CREATE DATABASE sleepbot_db;
CREATE USER sleepbot_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE sleepbot_db TO sleepbot_user;
\q
```

### 2. Clone and Configure

```bash
# Create directory
sudo mkdir -p /opt/sleepbot
sudo chown $USER:$USER /opt/sleepbot

# Clone repository
cd /opt/sleepbot
git clone https://github.com/Vilis322/sleepBot.git .
git checkout main  # After merging dev/setup to main

# Create production .env
cp .env.production.example .env
nano .env  # Edit with your values
```

### 3. Install and Setup

```bash
# Install dependencies
pip install -e .

# Create logs directory
mkdir -p logs

# Run migrations
alembic upgrade head
```

### 4. Start with PM2

```bash
# Start the bot
pm2 start ecosystem.config.js

# Save PM2 configuration
pm2 save

# Setup PM2 to start on boot
pm2 startup
# Follow the instructions from the command output

# Check logs
pm2 logs sleepbot
```

### 5. Configure GitHub Secrets

For CI/CD to work, add these secrets in your GitHub repository:

- `BOT_TOKEN`: Your Telegram bot token
- `SERVER_HOST`: Your server IP/domain
- `SERVER_USER`: SSH username
- `SSH_KEY`: Private SSH key for deployment

---

## Common Commands

```bash
# Development
make help         # Show all available commands
make run          # Run the bot
make test         # Run all tests
make db-up        # Start PostgreSQL
make db-migrate   # Create new migration
make format       # Format code with black
make lint         # Run linters

# Production
pm2 restart sleepbot     # Restart bot
pm2 logs sleepbot        # View logs
pm2 status               # Check status
pm2 monit                # Monitor resources
```

---

## Troubleshooting

### Bot not responding

```bash
# Check if bot is running
pm2 status

# Check logs
pm2 logs sleepbot --lines 100

# Restart bot
pm2 restart sleepbot
```

### Database connection errors

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check database exists
psql -U sleepbot_user -d sleepbot_db -c "SELECT 1;"

# Check migrations
alembic current
alembic history
```

### Port 5432 already in use

If you have another PostgreSQL instance:
- Use the existing PostgreSQL (recommended)
- Or change port in `docker-compose.yml` and `.env`

---

## Next Steps

1. **Merge to main**: After testing, merge `dev/setup` to `main`
2. **Setup monitoring**: Consider adding error tracking (Sentry, etc.)
3. **Backup strategy**: Setup automated PostgreSQL backups
4. **SSL/Security**: Ensure server security best practices

For questions or issues, check the logs first:
- Local: Terminal output
- Production: `pm2 logs sleepbot`
