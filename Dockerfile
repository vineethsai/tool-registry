FROM python:3.10-slim

WORKDIR /app

# Version information
LABEL version="2.0.0"
LABEL description="Production-ready Docker image for Tool Registry API with PostgreSQL and Redis integration"
LABEL maintainer="team@toolregistry.ai"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_VERSION=2.0.0 \
    DEBUG=false \
    AUTH_DISABLED=true \
    METRICS_ENABLED=true \
    DATABASE_URL=postgresql://postgres:password@db:5432/toolregistry \
    REDIS_URL=redis://redis:6379/0

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        python3-dev \
        libpq-dev \
        curl \
        netcat-traditional \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install email-validator explicitly first
RUN pip install --no-cache-dir email-validator==2.1.0

# Copy requirements and install dependencies
COPY requirements.txt .
COPY setup.py .
RUN pip install --no-cache-dir -e .
# Install additional required packages
RUN pip install --no-cache-dir PyJWT pydantic-settings psycopg2-binary redis hvac prometheus-client

# Copy the application code
COPY . .

# Make scripts executable
RUN chmod +x start.sh
RUN chmod +x init_admin.py

# Create a non-root user to run the application
RUN addgroup --system appgroup && \
    adduser --system --group appuser && \
    chown -R appuser:appgroup /app

# Create data directory for SQLite (fallback)
RUN mkdir -p /data && chmod -R 777 /data

# Ensure Postman collection files have correct permissions
RUN mkdir -p /app/postman && \
    chown -R appuser:appuser /app/postman

# Copy Postman files
COPY postman/tool_registry_api_collection.json /app/postman/
COPY postman/tool_registry_environment.json /app/postman/
COPY postman/README.md /app/postman/
COPY postman/server.py /app/postman/

# Verify that init_admin.py exists
RUN ls -la /app/init_admin.py || echo "WARNING: init_admin.py not found!"

# Switch to non-root user
USER appuser

# Expose the port the app runs on
EXPOSE 8000

# Add health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Command to run the application
CMD ["uvicorn", "tool_registry.main:app", "--host", "0.0.0.0", "--port", "8000"] 