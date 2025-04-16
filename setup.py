from setuptools import setup, find_packages

setup(
    name="tool_registry",
    version="1.0.8",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "pydantic",
        "pydantic-settings",
        "python-jose[cryptography]",
        "passlib[bcrypt]",
        "python-multipart",
        "redis",
        "hvac",
        "prometheus-client",
        "psycopg2-binary",
        "sqlalchemy",
        "python-dotenv",
        "email-validator",
    ],
    python_requires=">=3.8",
) 