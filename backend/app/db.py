"""
Database engine and session management.

Usage in FastAPI route:
    from app.db import get_session
    from sqlmodel import Session

    @router.get("/example")
    def example(session: Session = Depends(get_session)):
        ...
"""

import os
from sqlmodel import Session, SQLModel, create_engine

# Read from environment; fall back to a local SQLite DB for convenience
# during development without Docker.
DATABASE_URL: str = os.environ.get(
    "DATABASE_URL",
    "sqlite:///./literature_map_dev.db",
)

# Railway provides postgresql:// URLs; SQLAlchemy requires postgresql+psycopg2://
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

# connect_args: SQLite needs check_same_thread=False;
# PostgreSQL on Railway requires SSL.
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
else:
    connect_args = {"sslmode": "require"}

engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)


def create_db_and_tables() -> None:
    """Create all tables defined by SQLModel table=True classes.

    Called once at application startup via the FastAPI lifespan handler.
    For production schema migrations use Alembic instead.
    """
    # Import db_models so SQLModel's metadata is populated before create_all.
    import app.db_models  # noqa: F401
    SQLModel.metadata.create_all(engine)


def get_session():
    """FastAPI dependency that yields a database session per request."""
    with Session(engine) as session:
        yield session
