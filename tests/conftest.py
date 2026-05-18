import hashlib
import hmac
import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, get_db
from main import app

TEST_SECRET = "test-secret-abc"

TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=TEST_ENGINE)
    yield
    Base.metadata.drop_all(bind=TEST_ENGINE)


@pytest.fixture()
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setattr("config.settings.github_webhook_secret", TEST_SECRET)

    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def make_signature(body: bytes, secret: str = TEST_SECRET) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def post_webhook(client, event_type: str, payload: dict, secret: str = TEST_SECRET):
    body = json.dumps(payload).encode()
    sig = make_signature(body, secret)
    return client.post(
        "/webhooks",
        content=body,
        headers={
            "X-GitHub-Event": event_type,
            "X-Hub-Signature-256": sig,
            "Content-Type": "application/json",
        },
    )


REPO_PAYLOAD = {
    "id": 1001,
    "full_name": "org/repo",
    "html_url": "https://github.com/org/repo",
}

USER_PAYLOAD = {"login": "alice", "id": 42}

PR_PAYLOAD = {
    "id": 9001,
    "number": 7,
    "title": "Add feature",
    "state": "open",
    "html_url": "https://github.com/org/repo/pull/7",
    "user": USER_PAYLOAD,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-02T00:00:00Z",
    "merged_at": None,
}
