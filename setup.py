from setuptools import setup, find_packages

setup(
    name="tool_registry",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "pydantic",
        "python-jose[cryptography]",
        "passlib[bcrypt]",
        "python-multipart",
        "redis",
        "hvac",
        "prometheus-client",
        "psycopg2-binary",
        "sqlalchemy",
        "python-dotenv",
    ],
) 