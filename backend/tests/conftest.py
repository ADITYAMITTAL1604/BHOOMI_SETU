"""Pytest configuration and fixtures for BhoomiSetu backend test suite."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

# Ensure backend root is always at head of sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.config import get_settings
from app.core.security import create_access_token, hash_password
from app.database import Base, SessionLocal, engine, get_db
from app.main import app
from app.models.enums import UserRole
from app.models.user import User

settings = get_settings()


@pytest.fixture(scope="session")
def setup_database():
    """Ensure database schema is created for test session."""
    Base.metadata.create_all(bind=engine)
    yield
    # Teardown if needed


@pytest.fixture(scope="function")
def db_session(setup_database):
    """Provide a transactional database session per test function."""
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI TestClient with overridden database session."""
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_admin_user(db_session) -> User:
    """Create or return an ADMIN user for testing."""
    existing = db_session.query(User).filter(User.username == "test_admin").first()
    if existing:
        return existing
    user = User(
        id=uuid4(),
        username="test_admin",
        email="test_admin@bhoomisetu.gov.in",
        password_hash=hash_password("password123"),
        role=UserRole.ADMIN.value,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_state_user(db_session) -> User:
    """Create or return a STATE user scoped to Maharashtra."""
    existing = db_session.query(User).filter(User.username == "test_state_mh").first()
    if existing:
        return existing
    user = User(
        id=uuid4(),
        username="test_state_mh",
        email="state_mh@bhoomisetu.gov.in",
        password_hash=hash_password("password123"),
        role=UserRole.STATE.value,
        state_scope="Maharashtra",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_field_officer(db_session) -> User:
    """Create or return a FIELD_OFFICER user scoped to Pune, Maharashtra."""
    existing = db_session.query(User).filter(User.username == "test_field_pune").first()
    if existing:
        return existing
    user = User(
        id=uuid4(),
        username="test_field_pune",
        email="officer_pune@bhoomisetu.gov.in",
        password_hash=hash_password("password123"),
        role=UserRole.FIELD_OFFICER.value,
        state_scope="Maharashtra",
        district_scope="Pune",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_headers(test_admin_user) -> dict[str, str]:
    token = create_access_token({
        "sub": str(test_admin_user.id),
        "username": test_admin_user.username,
        "role": test_admin_user.role,
        "user_id": str(test_admin_user.id),
    })
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def state_user_headers(test_state_user) -> dict[str, str]:
    token = create_access_token({
        "sub": str(test_state_user.id),
        "username": test_state_user.username,
        "role": test_state_user.role,
        "user_id": str(test_state_user.id),
        "state_scope": test_state_user.state_scope,
    })
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def field_officer_headers(test_field_officer) -> dict[str, str]:
    token = create_access_token({
        "sub": str(test_field_officer.id),
        "username": test_field_officer.username,
        "role": test_field_officer.role,
        "user_id": str(test_field_officer.id),
        "state_scope": test_field_officer.state_scope,
        "district_scope": test_field_officer.district_scope,
    })
    return {"Authorization": f"Bearer {token}"}
