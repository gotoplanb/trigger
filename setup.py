from setuptools import setup, find_packages

setup(
    name="trigger",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.110.0",
        "uvicorn>=0.29.0",
        "pydantic>=2.6.0",
        "pydantic-settings>=2.1.0",
        "sqlalchemy>=2.0.0",
        "psycopg2-binary>=2.9.9",
        "alembic>=1.13.0",
        "psycopg-pool>=3.2.0",
        "httpx>=0.24.0",
        "python-dotenv>=1.0.0",
        "loguru>=0.7.0",
        "pyyaml>=6.0.0",
    ],
)
