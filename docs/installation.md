# Installation Guide

This guide will help you set up and run the GenAI Tool Registry on your local machine.

## Prerequisites

Before installing the Tool Registry, make sure you have the following installed:

- Python 3.9 or higher
- pip (Python package manager)
- Git (optional, for cloning the repository)
- A database (SQLite, PostgreSQL, or MySQL)

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/tool-registry.git
cd tool-registry
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -e ".[dev]"
```

This will install the package in development mode with all the necessary dependencies.

### 4. Configure the Database

By default, the Tool Registry uses SQLite, which doesn't require additional setup. For production use, it's recommended to use PostgreSQL or MySQL.

Create a `.env` file in the root directory with the following content:

```bash
# For SQLite (default)
DATABASE_URL=sqlite:///tool_registry.db

# For PostgreSQL
# DATABASE_URL=postgresql://username:password@localhost/tool_registry

# For MySQL
# DATABASE_URL=mysql://username:password@localhost/tool_registry

# Security settings
SECRET_KEY=your-secret-key-here
DEBUG=false
TEST_MODE=false
```

### 5. Run Database Migrations

```bash
alembic upgrade head
```

This will create all the necessary database tables.

### 6. Start the Server

```bash
python -m tool_registry.main
```

The API server will start running on `http://localhost:8000`.

## Verifying the Installation

Visit `http://localhost:8000/docs` in your browser to see the FastAPI automatic documentation. This will show all available endpoints and allow you to test them.

## Running Tests

To run the tests:

```bash
python -m pytest
```

For tests with coverage:

```bash
python -m pytest --cov=tool_registry
```

## Docker Installation (Alternative)

If you prefer using Docker, follow these steps:

### 1. Build the Docker Image

```bash
docker build -t tool-registry .
```

### 2. Run the Docker Container

```bash
docker run -p 8000:8000 -e DATABASE_URL=sqlite:///tool_registry.db -e SECRET_KEY=your-secret-key tool-registry
```

## Production Deployment

For production deployment, consider the following:

1. Use a production-grade database like PostgreSQL
2. Set up a reverse proxy (Nginx or Apache)
3. Configure HTTPS
4. Use environment variables for configuration
5. Consider using Docker Compose for orchestration

Example Docker Compose configuration:

```yaml
version: '3'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/tool_registry
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=false
    depends_on:
      - db
    
  db:
    image: postgres:14
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_USER=postgres
      - POSTGRES_DB=tool_registry

volumes:
  postgres_data:
```

## Troubleshooting

### Common Issues

1. **Database connection errors**: 
   - Check that your DATABASE_URL is correct
   - Ensure the database server is running
   - Verify that the user has appropriate permissions

2. **Import errors**: 
   - Make sure you've installed the package with `pip install -e .`
   - Check for missing dependencies

3. **Migration errors**:
   - If you get errors during migration, try deleting the SQLite database file (if using SQLite) and rerunning the migrations

### Getting Help

If you encounter issues not covered in this guide:

1. Check the [FAQs](faq.md)
2. Search for similar issues in the GitHub repository
3. Create a new issue with details about the problem

## Next Steps

Once you have the Tool Registry up and running, check out:

- [Developer Guide](developer_guide.md) for extending the system
- [API Reference](api_reference.md) for using the API
- [Schema Documentation](schema.md) for understanding the data model 