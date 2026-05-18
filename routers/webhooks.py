import json
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from middleware.signature import verify_github_signature
from models import PullRequest, PullRequestReview, PushEvent, Repository
from schemas.webhook_events import (
    PullRequestEvent,
    PullRequestReviewEvent,
    PushEventPayload,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def _upsert_repository(db: Session, repo_data) -> Repository:
    repo = db.get(Repository, repo_data.id)
    if repo is None:
        repo = Repository(id=repo_data.id, full_name=repo_data.full_name, html_url=repo_data.html_url)
        db.add(repo)
    else:
        repo.full_name = repo_data.full_name
        repo.html_url = repo_data.html_url
    return repo


def _upsert_pull_request(db: Session, pr_data, repo_id: int) -> PullRequest:
    pr = db.get(PullRequest, pr_data.id)
    if pr is None:
        pr = PullRequest(
            id=pr_data.id,
            repository_id=repo_id,
            number=pr_data.number,
            title=pr_data.title,
            state=pr_data.state,
            author=pr_data.user.login,
            html_url=pr_data.html_url,
            created_at=pr_data.created_at,
            updated_at=pr_data.updated_at,
            merged_at=pr_data.merged_at,
        )
        db.add(pr)
    else:
        pr.title = pr_data.title
        pr.state = pr_data.state
        pr.updated_at = pr_data.updated_at
        pr.merged_at = pr_data.merged_at
    return pr


def handle_pull_request(payload: dict, db: Session) -> None:
    event = PullRequestEvent.model_validate(payload)
    repo = _upsert_repository(db, event.repository)
    pr = _upsert_pull_request(db, event.pull_request, repo.id)
    db.commit()
    logger.info(
        "pull_request event processed",
        extra={
            "event_type": "pull_request",
            "action": event.action,
            "repo": event.repository.full_name,
            "pr_number": pr.number,
            "pr_state": pr.state,
        },
    )


def handle_push(payload: dict, db: Session) -> None:
    event = PushEventPayload.model_validate(payload)
    repo = _upsert_repository(db, event.repository)
    push = PushEvent(
        repository_id=repo.id,
        ref=event.ref,
        before=event.before,
        after=event.after,
        pusher=event.pusher.login,
        commit_count=len(event.commits),
        received_at=datetime.utcnow(),
    )
    db.add(push)
    db.commit()
    logger.info(
        "push event processed",
        extra={
            "event_type": "push",
            "repo": event.repository.full_name,
            "ref": event.ref,
            "commit_count": len(event.commits),
        },
    )


def handle_pull_request_review(payload: dict, db: Session) -> None:
    event = PullRequestReviewEvent.model_validate(payload)
    repo = _upsert_repository(db, event.repository)
    pr = _upsert_pull_request(db, event.pull_request, repo.id)
    db.flush()

    review = db.get(PullRequestReview, event.review.id)
    if review is None:
        review = PullRequestReview(
            id=event.review.id,
            pull_request_id=pr.id,
            state=event.review.state,
            author=event.review.user.login,
            body=event.review.body,
            submitted_at=event.review.submitted_at,
            html_url=event.review.html_url,
        )
        db.add(review)
    else:
        review.state = event.review.state
        review.body = event.review.body
        review.submitted_at = event.review.submitted_at
    db.commit()
    logger.info(
        "pull_request_review event processed",
        extra={
            "event_type": "pull_request_review",
            "action": event.action,
            "repo": event.repository.full_name,
            "pr_number": event.pull_request.number,
            "review_state": review.state,
        },
    )


_HANDLERS = {
    "pull_request": handle_pull_request,
    "push": handle_push,
    "pull_request_review": handle_pull_request_review,
}


@router.post("")
async def receive_webhook(request: Request, db: Session = Depends(get_db)):
    body = await verify_github_signature(request, settings.github_webhook_secret)
    event_type = request.headers.get("X-GitHub-Event", "")
    handler = _HANDLERS.get(event_type)
    if handler is None:
        logger.info("ignored unknown webhook event", extra={"event_type": event_type})
        return {"status": "ignored"}

    payload = json.loads(body)
    handler(payload, db)
    return {"status": "ok"}
