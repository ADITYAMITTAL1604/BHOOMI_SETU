"""SQLAlchemy 2.0 engine, session factory, and declarative base with GeoAlchemy2."""

from collections.abc import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

settings = get_settings()

# ── Engine ────────────────────────────────────────────────────────────────────
is_sqlite = settings.database_url.startswith("sqlite")

engine = create_engine(
    settings.database_url,
    pool_pre_ping=not is_sqlite,
    pool_size=10 if not is_sqlite else 5,
    max_overflow=20 if not is_sqlite else 0,
    echo=settings.log_level == "DEBUG",
    connect_args={"check_same_thread": False} if is_sqlite else {},
)


@event.listens_for(engine, "connect")
def _set_search_path(dbapi_conn, _connection_record) -> None:
    """Ensure PostGIS objects are visible on every new connection (PostgreSQL only)."""
    if not is_sqlite:
        cursor = dbapi_conn.cursor()
        cursor.execute("SET search_path TO public")
        cursor.close()


# ── Session factory ───────────────────────────────────────────────────────────
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


# ── Declarative base ──────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    """Shared base class for all ORM models."""


# ── FastAPI dependency ────────────────────────────────────────────────────────
def get_db() -> Generator[Session, None, None]:
    """Yield a database session and close it when the request is done."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> bool:
    """Return True if the database is reachable (used by /health)."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False