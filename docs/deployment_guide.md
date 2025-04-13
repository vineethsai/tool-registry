# Tool Registry Deployment Guide

> **WARNING**: Authentication is currently disabled for development purposes. Before deploying to production, you MUST re-enable authentication by reverting the changes in `tool_registry/api/app.py` that replaced `get_current_agent` with `get_default_admin_agent`.

This guide provides instructions for deploying the Tool Registry system in various environments.

## Local Development Setup

### Prerequisites

- Python 3.9+
- PostgreSQL
- Redis (optional, for rate limiting)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/tool-registry.git
   cd tool-registry
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Initialize the database:
   ```bash
   python -m tool_registry.core.database init
   ```

6. Run the development server:
   ```bash
   uvicorn tool_registry.main:app --reload
   ```

## Configuration Options

Key environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | SQLAlchemy database URL | `sqlite:///./tool_registry.db` |
| `REDIS_URL` | Redis URL for rate limiting | None |
| `JWT_SECRET_KEY` | Secret key for JWT tokens | (randomly generated) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT token expiration time | 30 |
| `RATE_LIMIT` | API rate limit per minute | 100 |
| `LOG_LEVEL` | Logging level | `INFO` |

## Production Deployment

### Docker Deployment

1. Build the Docker image:
   ```bash
   docker build -t tool-registry .
   ```

2. Run with Docker Compose:
   ```bash
   docker-compose up -d
   ```

### Kubernetes Deployment

1. Apply Kubernetes configurations:
   ```bash
   kubectl apply -f k8s/
   ```

2. Check deployment status:
   ```bash
   kubectl get pods -n tool-registry
   ```

### Cloud Provider Deployments

#### AWS

1. Set up an RDS PostgreSQL instance
2. Configure Elastic Beanstalk or ECS
3. Use CloudFront for caching and SSL

#### Google Cloud

1. Set up Cloud SQL
2. Deploy to Cloud Run or GKE
3. Configure Cloud CDN

## Security Considerations

> **WARNING**: Authentication is currently disabled for development purposes. Before deploying to production, you MUST re-enable authentication by reverting the changes in `tool_registry/api/app.py` that replaced `get_current_agent` with `get_default_admin_agent`.

See the [Security Guide](security_guide.md) for detailed security recommendations.

## Monitoring and Logging

1. Implement health checks:
   ```
   GET /health
   ```

2. Set up logging with your preferred provider (CloudWatch, Stackdriver, etc.)

3. Configure alerts for critical errors and performance issues

## Scaling Considerations

- Database connection pooling
- Horizontal scaling with load balancers
- Redis caching for frequently accessed data
- CDN for static assets

## Backup and Recovery

1. Regular database backups
2. Point-in-time recovery options
3. Disaster recovery plan

## Troubleshooting

Common issues:

- Database connection errors
- Redis connection failures
- JWT token validation issues
- Rate limiting problems

Check logs and the `/health` endpoint for diagnostics.

## Updating

1. Deploy new version
2. Run database migrations if needed
3. Monitor for any issues
4. Have a rollback plan

## Support

For deployment support, contact support@example.com. 