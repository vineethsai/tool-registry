# Tool Registry Production Setup

This document outlines the production deployment setup for the Tool Registry application with PostgreSQL and Redis integration.

## Version 2.0.0

The production environment is configured with:

- Tool Registry API (v2.0.0)
- PostgreSQL 14 database
- Redis 7 for caching
- Frontend UI (React application)

## Features

- Authentication disabled for easier access
- Metrics enabled for monitoring
- Health checks for all services
- PostgreSQL for reliable data storage
- Redis for caching and performance

## Deployment

### Prerequisites

- Docker and Docker Compose installed
- At least 2GB of RAM available for all services
- Open ports: 8000 (API), 3000 (Frontend), 5432 (PostgreSQL), 6379 (Redis)

### Starting the Environment

To start the production environment:

```bash
docker compose -f docker-compose.prod.yml up -d
```

This command will:
1. Pull or build all required images
2. Create volumes for persistent data
3. Start all services with proper dependencies
4. Set up health checks for monitoring

### Checking Status

To check if all services are running:

```bash
docker compose -f docker-compose.prod.yml ps
```

### Accessing the Application

- Frontend UI: http://localhost:3000
- API: http://localhost:8000
- Health check: http://localhost:8000/health

### Environment Variables

The production setup uses these environment variables:

#### API Service
- `JWT_SECRET`: Secret key for JWT tokens
- `AUTH_DISABLED`: Set to "true" to disable authentication
- `METRICS_ENABLED`: Set to "true" to enable metrics
- Database connection details (PostgreSQL)
- Redis connection details

#### Database Service
- `POSTGRES_USER`: Database username
- `POSTGRES_PASSWORD`: Database password 
- `POSTGRES_DB`: Database name

### Data Persistence

The following volumes are created for data persistence:

- `tool_registry_data`: Application data
- `postgres_data`: PostgreSQL database files
- `redis_data`: Redis data

### Stopping the Environment

To stop all services:

```bash
docker compose -f docker-compose.prod.yml down
```

To stop and remove all volumes (will delete all data):

```bash
docker compose -f docker-compose.prod.yml down -v
```

## Troubleshooting

### Health Checks

All services have health checks configured. You can verify their status with:

```bash
docker ps
```

Look for the "status" column to see if services are healthy.

### Logs

To view logs for a specific service:

```bash
docker logs tool-registry-app
docker logs tool-registry-db
docker logs tool-registry-redis
docker logs tool-registry-frontend
```

### Common Issues

1. **Database connection issues**: Check if PostgreSQL is healthy and the connection parameters are correct
2. **Redis connection issues**: Verify Redis is running and accessible
3. **Frontend not loading**: Check if the API URL is correctly set in the frontend environment 