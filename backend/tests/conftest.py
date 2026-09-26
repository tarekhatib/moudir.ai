import os

# Configure the app before importing it: in-memory database, no cross-origin config.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["CORS_ORIGINS"] = ""

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.security import login_limiter  # noqa: E402

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

PASSWORD = "correct-horse-battery"


def override_get_db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    """Fresh tables and rate-limit state for every test."""
    Base.metadata.create_all(bind=engine)
    login_limiter.reset()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def anon_client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def make_client():
    """Factory for a client signed in as the owner of a new organization."""
    clients = []

    def _make(org: str = "Acme", email: str = "owner@acme.example") -> TestClient:
        test_client = TestClient(app)
        clients.append(test_client)
        response = test_client.post(
            "/auth/signup",
            json={"organization_name": org, "name": "Owner", "email": email, "password": PASSWORD},
        )
        assert response.status_code == 201, response.text
        return test_client

    yield _make
    for test_client in clients:
        test_client.close()


@pytest.fixture
def client(make_client):
    """Client signed in as the owner of the "Acme" organization."""
    return make_client()


def agent_headers(test_client: TestClient, employee_id: int) -> dict:
    token = test_client.post(f"/employees/{employee_id}/agent-token").json()["agent_token"]
    return {"X-Agent-Token": token}
