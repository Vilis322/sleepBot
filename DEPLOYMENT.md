# Deployment Guide

## Docker Production Deployment

### Prerequisites on Server

1. **Install Docker and Docker Compose**
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt-get update
sudo apt-get install docker-compose-plugin
```

2. **Clone repository**
```bash
sudo mkdir -p /opt/sleepbot
sudo chown $USER:$USER /opt/sleepbot
cd /opt/sleepbot
git clone <your-repo-url> .
```

3. **Configure environment**
```bash
# Copy example env file
cp .env.production.example .env

# Edit with your credentials
nano .env
```

**Required environment variables:**
- `BOT_TOKEN` - Get from @BotFather on Telegram
- `DB_PASSWORD` - Strong password for PostgreSQL
- `DB_USER` - Database user (default: sleepbot_user)
- `DB_NAME` - Database name (default: sleepbot_db)

### First-Time Server Setup

```bash
# 1. Connect to your server
ssh user@your-server-ip

# 2. Update system
sudo apt update && sudo apt upgrade -y

# 3. Install Docker (if not installed)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 4. Install Docker Compose
sudo apt-get install docker-compose-plugin

# 5. Logout and login again for Docker group to take effect
exit
ssh user@your-server-ip

# 6. Verify Docker installation
docker --version
docker compose version

# 7. Create project directory
sudo mkdir -p /opt/sleepbot
sudo chown $USER:$USER /opt/sleepbot
cd /opt/sleepbot

# 8. Clone repository
git clone https://github.com/Vilis322/sleepBot.git .

# 9. Create .env file
nano .env
```

**Paste this into .env file:**
```env
# Telegram Bot Token (get from @BotFather)
BOT_TOKEN=your_bot_token_here

# Database Configuration
DB_NAME=sleepbot_db
DB_USER=sleepbot_user
DB_PASSWORD=your_strong_password_here

# Environment
ENVIRONMENT=production
LOG_LEVEL=INFO
```

Save and exit (Ctrl+X, then Y, then Enter).

### Deploy

```bash
# Build and start containers
docker compose -f docker-compose.production.yml up -d

# View logs
docker compose -f docker-compose.production.yml logs -f

# Check status
docker compose -f docker-compose.production.yml ps
```

### Verify Deployment

```bash
# Check bot is running
docker compose -f docker-compose.production.yml ps bot

# Check database is healthy
docker compose -f docker-compose.production.yml ps postgres

# View bot logs (look for "Bot started successfully")
docker compose -f docker-compose.production.yml logs bot | grep -i "started"

# Test database connection
docker compose -f docker-compose.production.yml exec postgres psql -U sleepbot_user -d sleepbot_db -c "SELECT 1;"
```

### Management Commands

```bash
# Restart bot
docker compose -f docker-compose.production.yml restart bot

# Stop everything
docker compose -f docker-compose.production.yml down

# Update and redeploy
git pull origin main
docker compose -f docker-compose.production.yml down
docker compose -f docker-compose.production.yml build --no-cache
docker compose -f docker-compose.production.yml up -d

# View bot logs
docker compose -f docker-compose.production.yml logs -f bot

# View database logs
docker compose -f docker-compose.production.yml logs -f postgres

# Access database
docker compose -f docker-compose.production.yml exec postgres psql -U sleepbot_user -d sleepbot_db

# Run migrations manually (if needed)
docker compose -f docker-compose.production.yml exec bot alembic upgrade head
```

### Backup Database

```bash
# Create backup
docker compose -f docker-compose.production.yml exec postgres pg_dump -U sleepbot_user sleepbot_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore from backup
docker compose -f docker-compose.production.yml exec -T postgres psql -U sleepbot_user sleepbot_db < backup.sql
```

## GitHub Actions CI/CD

The repository includes automated deployment via GitHub Actions.

### Required Secrets

Configure these in GitHub repository settings (Settings → Secrets → Actions):

- `SERVER_HOST` - Your server IP or domain
- `SERVER_USER` - SSH user (usually root or ubuntu)
- `SSH_KEY` - Private SSH key for authentication
- `BOT_TOKEN` - Telegram bot token (for tests)

### Test Coverage Requirements

- **Minimum Coverage**: 30% (configured in pyproject.toml)
- **Active Tests**: Mock tests (122 tests) + Unit tests (80 tests)
- **Disabled Tests**: Integration and smoke tests (commented out, not yet implemented)

### Workflow

1. Push to `main` branch triggers deployment
2. **Test Stage**:
   - Linters: black, flake8 (continue-on-error)
   - Mock tests: services, repositories, models (122 tests)
   - Unit tests: formatters, keyboards, logger (80 tests)
   - Coverage check: fails if below 30%
3. **Deploy Stage** (only if tests pass):
   - SSH to production server
   - Pull latest code from main
   - Rebuild Docker containers
   - Restart services
   - Show last 50 log lines

### Enabling Future Tests

To enable integration/smoke tests when ready, uncomment in `.github/workflows/main.yml`:

```yaml
# Uncomment these sections:
# - name: Run integration tests
# - name: Run smoke tests
```

## Local Development

See main README.md for local development setup with `make` commands.
