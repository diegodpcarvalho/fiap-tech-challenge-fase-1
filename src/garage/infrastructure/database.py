from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from garage.config import get_settings


class Base(DeclarativeBase):
    pass


def _build_engine() -> Engine:
    url = get_settings().database_url
    options: dict[str, object] = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False}
    if url == "sqlite://":
        options["poolclass"] = StaticPool
    built_engine = create_engine(url, **options)
    if url.startswith("sqlite"):
        event.listen(
            built_engine,
            "connect",
            lambda connection, _record: connection.execute("PRAGMA foreign_keys=ON"),
        )
    return built_engine


engine = _build_engine()
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def initialize_database() -> None:
    from garage.infrastructure import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
