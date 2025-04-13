# Installation Guide

This guide provides detailed instructions for installing and configuring the GenAI Tool Registry.

## Prerequisites

Before you begin, ensure that your system meets the following requirements:

- Python 3.9 or higher
- pip package manager
- Git (for cloning the repository)
- PostgreSQL (optional, for production environments)
- Redis (optional, for rate limiting)
- HashiCorp Vault (optional, for secret management)

## Basic Installation

Follow these steps to install the GenAI Tool Registry:

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/tool-registry.git
cd tool-registry
```

### 2. Create a Virtual Environment

It's recommended to use a virtual environment to isolate dependencies:

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Required Dependencies

```bash
# Install runtime dependencies
pip install -r requirements.txt

# For development and testing
pip install -r requirements-test.txt
```

### 4. Install the Package (Development Mode)

```bash
pip install -e .
```

## Configuration

The GenAI Tool Registry uses environment variables for configuration. You can set these in a `.env` file in the project root directory.

### Basic Configuration

Create a `.env` file with the following settings:

```
# Database Configuration
DATABASE_URL=sqlite:///./tool_registry.db

# JWT Configuration
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=30

# Logging
LOG_LEVEL=INFO
```

### Advanced Configuration

For production environments, consider the following additional settings:

```
# Database (PostgreSQL recommended for production)
DATABASE_URL=postgresql://username:password@localhost:5432/tool_registry

# Redis for rate limiting
REDIS_URL=redis://localhost:6379/0
RATE_LIMIT=100
RATE_LIMIT_WINDOW=60

# HashiCorp Vault for secret management
VAULT_URL=http://localhost:8200
VAULT_TOKEN=your-vault-token
VAULT_MOUNT_POINT=secret
```

## Database Setup

### SQLite (Development)

SQLite is used by default for development and requires no additional setup.

### PostgreSQL (Production)

For production environments, PostgreSQL is recommended:

1. Install PostgreSQL on your server
2. Create a database and user:

```sql
CREATE DATABASE tool_registry;
CREATE USER tool_registry_user WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE tool_registry TO tool_registry_user;
```

3. Update your `.env` file with the PostgreSQL connection string:

```
DATABASE_URL=postgresql://tool_registry_user:password@localhost:5432/tool_registry
```

## HashiCorp Vault Setup (Optional)

If you want to use HashiCorp Vault for secret management:

1. Install and start Vault
2. Create a token for the Tool Registry
3. Enable the KV secrets engine:

```bash
vault secrets enable -path=secret kv-v2
```

4. Store your secrets:

```bash
vault kv put secret/tool-registry/jwt secret_key=your-secret-key
```

5. Update your `.env` file with Vault settings:

```
VAULT_URL=http://localhost:8200
VAULT_TOKEN=your-vault-token
VAULT_MOUNT_POINT=secret
```

## Verifying Installation

To verify that your installation is working correctly:

1. Start the application:

```bash
uvicorn tool_registry.api.app:app --reload
```

2. Open a web browser and navigate to `http://localhost:8000/docs` to see the API documentation.

3. Run the tests to ensure everything is working:

```bash
pytest
```

## Docker Installation (Optional)

For containerized deployment, you can use Docker:

```bash
# Build the Docker image
docker build -t tool-registry .

# Run the container
docker run -p 8000:8000 -d --name tool-registry tool-registry
```

A `docker-compose.yml` file is also provided for setting up the complete environment including PostgreSQL and Redis.

## Troubleshooting

If you encounter any issues during installation:

1. Check that your Python version is 3.9 or higher
2. Ensure that all required dependencies are installed
3. Verify that your database connection string is correct
4. Check the logs for any error messages

Common issues:

- **Database connection errors**: Check that your database server is running and accessible
- **Import errors**: Ensure that all dependencies are installed and the virtual environment is activated
- **Permission issues**: Check file and directory permissions for the application and database

For additional help, refer to the project's GitHub Issues page or contact the maintainers. 