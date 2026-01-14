# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml ./

# Install Python dependencies (production only)
RUN pip install --upgrade pip setuptools wheel && \
    python -c "import tomllib; \
    f = open('pyproject.toml', 'rb'); \
    data = tomllib.load(f); \
    deps = data['project']['dependencies']; \
    print(' '.join(deps))" > /tmp/deps.txt && \
    cat /tmp/deps.txt | xargs pip install && \
    rm /tmp/deps.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Run database migrations and start the bot
CMD sh -c "sleep 2 && alembic upgrade head && python main.py"
