import pytest

from models import PullRequest, Repository
from tests.conftest import PR_PAYLOAD, REPO_PAYLOAD, USER_PAYLOAD, post_webhook


def _pr_event(action: str, merged_at=None):
    pr = {**PR_PAYLOAD, "merged_at": merged_at}
    if action == "closed" and merged_at:
        pr["state"] = "closed"
    elif action == "closed":
        pr["state"] = "closed"
    elif action == "reopened":
        pr["state"] = "open"
    return {
        "action": action,
        "pull_request": pr,
        "repository": REPO_PAYLOAD,
        "sender": USER_PAYLOAD,
    }


def test_pull_request_opened(client, db_session):
    resp = post_webhook(client, "pull_request", _pr_event("opened"))
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

    repo = db_session.get(Repository, REPO_PAYLOAD["id"])
    assert repo is not None
    assert repo.full_name == "org/repo"

    pr = db_session.get(PullRequest, PR_PAYLOAD["id"])
    assert pr is not None
    assert pr.number == PR_PAYLOAD["number"]
    assert pr.state == "open"
    assert pr.author == "alice"


def test_pull_request_closed(client, db_session):
    post_webhook(client, "pull_request", _pr_event("opened"))
    resp = post_webhook(client, "pull_request", _pr_event("closed"))
    assert resp.status_code == 200

    pr = db_session.get(PullRequest, PR_PAYLOAD["id"])
    assert pr.state == "closed"


def test_pull_request_reopened(client, db_session):
    post_webhook(client, "pull_request", _pr_event("opened"))
    post_webhook(client, "pull_request", _pr_event("closed"))
    resp = post_webhook(client, "pull_request", _pr_event("reopened"))
    assert resp.status_code == 200

    pr = db_session.get(PullRequest, PR_PAYLOAD["id"])
    assert pr.state == "open"
