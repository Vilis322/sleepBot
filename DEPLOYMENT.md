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

### Deploy

```bash
# Build and start containers
docker compose -f docker-compose.production.yml up -d

# View logs
docker compose -f docker-compose.production.yml logs -f

# Check status
docker compose -f docker-compose.production.yml ps
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

### Workflow

1. Push to `main` branch triggers deployment
2. Tests run automatically
3. If tests pass, deploys to production server via SSH
4. Docker containers rebuild and restart automatically

## Local Development

See main README.md for local development setup with `make` commands.
