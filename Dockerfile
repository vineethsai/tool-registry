FROM python:3.9-slim

WORKDIR /app

# Version information
LABEL version="2.0.1"
LABEL description="Tool Registry API with comprehensive API endpoint testing and improved compatibility"
LABEL maintainer="Vineeth Sai Narajala"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    netcat-openbsd \
    curl \
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
RUN adduser --disabled-password --gecos "" appuser
RUN chown -R appuser:appuser /app

# Create data directory for SQLite
RUN mkdir -p /app/data && chown -R appuser:appuser /app/data

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

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DATABASE_URL=sqlite:///./data/tool_registry.db
ENV APP_VERSION=2.0.1

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Command to run the application
CMD ["./start.sh"] 