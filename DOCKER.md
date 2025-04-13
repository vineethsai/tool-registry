# Docker Setup for GenAI Tool Registry

This document describes how to run the GenAI Tool Registry using Docker and Docker Compose.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Getting Started

### Using PostgreSQL (Recommended for Production)

To start the application with PostgreSQL and Redis:

```bash
docker compose up -d
```

This will:
- Build the application container
- Start a PostgreSQL database container
- Start a Redis container for caching
- Connect the application to both services

### Using SQLite (Simpler Setup for Development)

For a simpler setup using SQLite instead of PostgreSQL:

```bash
docker compose -f docker-compose.sqlite.yml up -d
```

This uses SQLite as the database, which is stored in the `data` directory on your host machine.

## Accessing the Application

The application will be available at:

- API: http://localhost:8000
- Swagger Documentation: http://localhost:8000/docs
- ReDoc API Documentation: http://localhost:8000/redoc

## Environment Variables

You can customize the application by modifying the environment variables in the docker-compose file:

- `DATABASE_URL`: Database connection string
- `REDIS_URL`: Redis connection string
- `JWT_SECRET_KEY`: Secret key for JWT token generation

## Working with the Containers

### View Logs

```bash
# All services
docker compose logs

# Just the application
docker compose logs app

# Follow logs
docker compose logs -f app
```

### Restart a Service

```bash
docker compose restart app
```

### Stop the Application

```bash
docker compose down
```

### Stop and Remove Volumes

```bash
docker compose down -v
```

## Data Persistence

- PostgreSQL data is stored in a named volume: `postgres_data`
- Redis data is stored in a named volume: `redis_data`
- SQLite data is stored in the `./data` directory

## Troubleshooting

### Database Connection Issues

If you're experiencing database connection issues, you can check if the database is running:

```bash
docker compose ps db
```

### Checking Database Contents

PostgreSQL:
```bash
docker compose exec db psql -U postgres -d tool_registry
```

For SQLite, you can use a SQLite client on your host machine to access the database file in the `data` directory.

### Re-building the Container

If you make changes to the application code, you may need to rebuild the container:

```bash
docker compose build
``` 