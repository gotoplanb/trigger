from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# Import models for Alembic to auto-generate migrations
from app.models.base import Base
from app.models.trigger import Trigger, TriggerEvent

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Check if we're running in test mode
import os

TESTING = os.environ.get("TESTING", "").lower() == "true"

# Override sqlalchemy.url from environment variable
from app.core.config import settings

sqlalchemy_url = settings.DATABASE_URL
if sqlalchemy_url.startswith("postgres://"):
    sqlalchemy_url = sqlalchemy_url.replace("postgres://", "postgresql://", 1)
config.set_main_option("sqlalchemy.url", sqlalchemy_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
