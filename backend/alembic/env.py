import os
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy import create_engine
from sqlmodel import SQLModel

from alembic import context

# Import all ORM models so their tables are registered in SQLModel.metadata.
import app.db_models  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Use SQLModel's shared metadata for autogenerate support.
target_metadata = SQLModel.metadata

# DATABASE_URL must be set — fail loudly if missing so the pre-deploy
# command aborts rather than silently connecting to the wrong host.
db_url = os.environ.get("DATABASE_URL")
if not db_url:
    raise RuntimeError(
        "DATABASE_URL environment variable is not set. "
        "Set it in your Railway service variables."
    )

# Railway provides postgresql:// URLs; SQLAlchemy requires postgresql+psycopg2://
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

config.set_main_option("sqlalchemy.url", db_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (no live DB connection required)."""
    context.configure(
        url=db_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (connects to the database)."""
    connect_args = {"sslmode": "require"} if db_url.startswith("postgresql") else {}
    connectable = create_engine(db_url, poolclass=pool.NullPool, connect_args=connect_args)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
