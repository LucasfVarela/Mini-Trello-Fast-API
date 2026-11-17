from collections.abc import Callable, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.db import Base, get_db
from app.main import app


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def client(db_session: Session, tmp_path, monkeypatch) -> Generator[TestClient, None, None]:
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "uploads"))
    app.dependency_overrides[get_db] = lambda: db_session
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def register_user(client: TestClient) -> Callable[[str], dict]:
    def _register(username: str, password: str = "password123") -> dict:
        response = client.post(
            "/api/v1/auth/register",
            json={"username": username, "email": f"{username}@example.com", "password": password},
        )
        assert response.status_code == 201, response.text
        login = client.post(
            "/api/v1/auth/login",
            data={"username": username, "password": password},
        )
        assert login.status_code == 200, login.text
        user = response.json()
        user["headers"] = {"Authorization": f"Bearer {login.json()['access_token']}"}
        return user

    return _register


@pytest.fixture
def alice(register_user) -> dict:
    return register_user("alice")


@pytest.fixture
def bob(register_user) -> dict:
    return register_user("bob")


@pytest.fixture
def project(client: TestClient, alice: dict) -> dict:
    response = client.post(
        "/api/v1/projects",
        json={"name": "Trabajo práctico", "description": "Proyecto de la facultad"},
        headers=alice["headers"],
    )
    assert response.status_code == 201, response.text
    return response.json()
