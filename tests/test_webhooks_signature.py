import json

from tests.conftest import PR_PAYLOAD, REPO_PAYLOAD, USER_PAYLOAD, make_signature


def _pr_event_body():
    return json.dumps(
        {
            "action": "opened",
            "pull_request": PR_PAYLOAD,
            "repository": REPO_PAYLOAD,
            "sender": USER_PAYLOAD,
        }
    ).encode()


def test_valid_signature_returns_200(client):
    body = _pr_event_body()
    sig = make_signature(body)
    resp = client.post(
        "/webhooks",
        content=body,
        headers={
            "X-GitHub-Event": "pull_request",
            "X-Hub-Signature-256": sig,
            "Content-Type": "application/json",
        },
    )
    assert resp.status_code == 200


def test_invalid_signature_returns_403(client):
    body = _pr_event_body()
    resp = client.post(
        "/webhooks",
        content=body,
        headers={
            "X-GitHub-Event": "pull_request",
            "X-Hub-Signature-256": "sha256=deadbeef",
            "Content-Type": "application/json",
        },
    )
    assert resp.status_code == 403


def test_missing_signature_returns_403(client):
    body = _pr_event_body()
    resp = client.post(
        "/webhooks",
        content=body,
        headers={
            "X-GitHub-Event": "pull_request",
            "Content-Type": "application/json",
        },
    )
    assert resp.status_code == 403
