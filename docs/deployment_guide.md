# Tool Registry Deployment Guide

This guide provides detailed instructions for deploying the Tool Registry system in various environments.

## Deployment Options

### Local Development Environment

For local development and testing:

```bash
# Clone the repository
git clone https://github.com/example/tool-registry.git
cd tool-registry

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up database
export DATABASE_URL="postgresql://localhost/tool_registry_dev"
python -m tool_registry.db.init_db

# Run the development server
python -m tool_registry.main
```

### Docker Deployment

For containerized deployment:

```bash
# Build the Docker image
docker build -t tool-registry:latest .

# Run the container
docker run -d \
  --name tool-registry \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql://user:password@db-host/tool_registry" \
  -e SECRET_KEY="your-secret-key" \
  -e ENVIRONMENT="production" \
  tool-registry:latest
```

Using Docker Compose:

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db/tool_registry
      - SECRET_KEY=your-secret-key
      - ENVIRONMENT=production
    depends_on:
      - db
    restart: always

  db:
    image: postgres:13
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=tool_registry
    restart: always

volumes:
  postgres_data:
```

Run with:

```bash
docker-compose up -d
```

### Kubernetes Deployment

For production-grade cloud deployment:

```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tool-registry
  labels:
    app: tool-registry
spec:
  replicas: 3
  selector:
    matchLabels:
      app: tool-registry
  template:
    metadata:
      labels:
        app: tool-registry
    spec:
      containers:
      - name: tool-registry
        image: tool-registry:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: tool-registry-secrets
              key: database-url
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: tool-registry-secrets
              key: secret-key
        - name: ENVIRONMENT
          value: production
        resources:
          limits:
            cpu: "1"
            memory: "1Gi"
          requests:
            cpu: "500m"
            memory: "512Mi"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

Service configuration:

```yaml
# kubernetes/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: tool-registry
spec:
  selector:
    app: tool-registry
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
```

Apply with:

```bash
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/service.yaml
```

## Environment Configuration

### Required Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | PostgreSQL connection URL | - | Yes |
| `SECRET_KEY` | Secret key for JWT signing | - | Yes |
| `ENVIRONMENT` | Deployment environment | development | No |
| `LOG_LEVEL` | Logging level | INFO | No |
| `PORT` | Server port | 8000 | No |
| `ALLOWED_ORIGINS` | CORS allowed origins | * | No |
| `JWT_EXPIRATION` | JWT token expiration in seconds | 3600 | No |
| `RATE_LIMIT_PER_MINUTE` | API rate limit per minute | 100 | No |

### Database Configuration

The Tool Registry requires PostgreSQL 12+ as its database. Set up the database:

```sql
CREATE DATABASE tool_registry;
CREATE USER tool_registry_user WITH ENCRYPTED PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE tool_registry TO tool_registry_user;
```

Update the `DATABASE_URL` environment variable:

```
DATABASE_URL=postgresql://tool_registry_user:your_password@localhost/tool_registry
```

### TLS/SSL Configuration

For production deployments, enable TLS:

1. Using Nginx as a reverse proxy:

```nginx
server {
    listen 443 ssl;
    server_name tool-registry.example.com;

    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

2. Using Traefik in Kubernetes:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: tool-registry-ingress
  annotations:
    kubernetes.io/ingress.class: "traefik"
    traefik.ingress.kubernetes.io/router.tls: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - tool-registry.example.com
    secretName: tool-registry-tls
  rules:
  - host: tool-registry.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: tool-registry
            port:
              number: 80
```

## Scaling Configuration

### Horizontal Scaling

For horizontal scaling with multiple instances:

1. Ensure the database can handle multiple connections
2. Use a load balancer to distribute traffic
3. Configure session persistence if needed

Kubernetes scaling example:

```bash
kubectl scale deployment tool-registry --replicas=5
```

Or set up autoscaling:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: tool-registry-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: tool-registry
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### Database Scaling

For high-availability database setup:

1. **Read Replicas**: Configure PostgreSQL read replicas
2. **Connection Pooling**: Use PgBouncer for connection pooling
3. **Sharding**: For very large deployments, consider database sharding

## Backup and Disaster Recovery

### Database Backups

Schedule regular database backups:

```bash
# Automated backup script example
pg_dump -U postgres tool_registry > /backups/tool_registry_$(date +%Y%m%d_%H%M%S).sql
```

Or using a Kubernetes CronJob:

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: db-backup
spec:
  schedule: "0 2 * * *"  # Every day at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: db-backup
            image: postgres:13
            command:
            - /bin/sh
            - -c
            - pg_dump -h db -U postgres -d tool_registry > /backups/tool_registry_$(date +%Y%m%d).sql
            volumeMounts:
            - name: backup-volume
              mountPath: /backups
          volumes:
          - name: backup-volume
            persistentVolumeClaim:
              claimName: backup-pvc
          restartPolicy: OnFailure
```

### Disaster Recovery

Create a disaster recovery plan:

1. **Regular Backups**: Store backups in multiple locations
2. **Backup Testing**: Regularly test backup restoration
3. **Failover Procedure**: Document the process for failover
4. **Recovery Time Objective (RTO)**: Define acceptable downtime
5. **Recovery Point Objective (RPO)**: Define acceptable data loss

## Monitoring and Logging

### Prometheus Metrics

The Tool Registry exposes metrics at `/metrics`:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'tool-registry'
    scrape_interval: 15s
    static_configs:
      - targets: ['tool-registry:8000']
```

### Log Aggregation

Configure centralized logging:

1. **ELK Stack**: Elasticsearch, Logstash, Kibana
2. **Loki**: For Kubernetes environments with Grafana

Fluentd configuration example:

```
<source>
  @type tail
  path /var/log/tool-registry.log
  pos_file /var/log/td-agent/tool-registry.log.pos
  tag tool-registry
  <parse>
    @type json
  </parse>
</source>

<match tool-registry>
  @type elasticsearch
  host elasticsearch
  port 9200
  logstash_format true
  logstash_prefix tool-registry
  include_tag_key true
  type_name access_log
  tag_key @log_name
</match>
```

## Maintenance

### Database Maintenance

Regular database maintenance tasks:

```sql
-- Analyze tables
ANALYZE VERBOSE;

-- Vacuum tables
VACUUM ANALYZE;

-- Reindex
REINDEX DATABASE tool_registry;
```

### Application Updates

Process for updating the application:

1. **Backup**: Create a backup before updating
2. **Testing**: Test the update in a staging environment
3. **Deployment**: Deploy using a blue-green or canary strategy
4. **Verification**: Verify the application is working correctly
5. **Rollback Plan**: Document the rollback procedure

## Troubleshooting

Common issues and solutions:

| Issue | Possible Cause | Solution |
|-------|----------------|----------|
| Database connection errors | Incorrect credentials or unreachable database | Verify DATABASE_URL and network connectivity |
| Server won't start | Port conflict or missing dependencies | Check if port 8000 is in use; verify all dependencies are installed |
| Authentication failures | Expired JWT token or incorrect secret key | Verify SECRET_KEY and token expiration settings |
| Rate limiting issues | Misconfigured rate limits | Adjust RATE_LIMIT_PER_MINUTE environment variable |
| Slow API responses | Database performance or resource constraints | Check database indexes, query performance, and server resources |

## Health Checks

The `/health` endpoint provides system health information:

```bash
curl http://localhost:8000/health
```

Response:

```json
{
  "status": "healthy",
  "version": "1.2.3",
  "uptime": 1234567,
  "db_connection": "connected",
  "components": {
    "database": {
      "status": "healthy",
      "latency_ms": 5
    },
    "api": {
      "status": "healthy",
      "requests_per_minute": 250
    }
  }
}
```

## Advanced Configuration

### Custom Authentication Providers

To integrate with external authentication providers:

1. Implement a custom authentication backend
2. Configure the AUTH_PROVIDER environment variable
3. Set the required provider-specific environment variables

Example for OAuth provider:

```
AUTH_PROVIDER=oauth2
OAUTH_CLIENT_ID=your-client-id
OAUTH_CLIENT_SECRET=your-client-secret
OAUTH_AUTHORIZE_URL=https://auth.example.com/authorize
OAUTH_TOKEN_URL=https://auth.example.com/token
```

### API Rate Limiting

Configure advanced rate limiting:

```
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_PER_HOUR=1000
RATE_LIMIT_STRATEGY=sliding_window
RATE_LIMIT_BY_IP=true
RATE_LIMIT_BY_TOKEN=true
```

### Custom Database Migrations

For custom database migrations:

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migrations
alembic downgrade -1
``` 