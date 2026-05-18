from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from models.pull_request import PullRequest
from schemas.pulls import PullStats
from services.github_client import GitHubClient

router = APIRouter()


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    return datetime.fromisoformat(value.rstrip("Z")).replace(tzinfo=timezone.utc)


@router.get("/pulls/{owner}/{repo}", response_model=PullStats)
async def get_pull_stats(owner: str, repo: str, db: Session = Depends(get_db)) -> PullStats:
    repo_key = f"{owner}/{repo}"

    async with GitHubClient(token=settings.github_token) as client:
        pulls = await client.get_pulls(owner, repo)
        for pr in pulls:
            reviews = await client.get_reviews(owner, repo, pr["number"])
            first_review_at: Optional[datetime] = None
            for review in sorted(reviews, key=lambda r: r.get("submitted_at", "")):
                submitted = _parse_dt(review.get("submitted_at"))
                if submitted:
                    first_review_at = submitted
                    break

            existing = db.scalar(
                select(PullRequest).where(
                    PullRequest.repo == repo_key,
                    PullRequest.number == pr["number"],
                )
            )
            if existing is None:
                existing = PullRequest(repo=repo_key, number=pr["number"])
                db.add(existing)

            existing.state = pr["state"]
            existing.created_at = _parse_dt(pr["created_at"])
            existing.merged_at = _parse_dt(pr.get("merged_at"))
            existing.additions = pr.get("additions", 0) or 0
            existing.deletions = pr.get("deletions", 0) or 0
            existing.first_review_at = first_review_at

        db.commit()

    open_count = db.scalar(
        select(func.count()).where(PullRequest.repo == repo_key, PullRequest.state == "open")
    ) or 0
    closed_count = db.scalar(
        select(func.count()).where(
            PullRequest.repo == repo_key,
            PullRequest.state == "closed",
            PullRequest.merged_at.is_(None),
        )
    ) or 0
    merged_count = db.scalar(
        select(func.count()).where(
            PullRequest.repo == repo_key, PullRequest.merged_at.is_not(None)
        )
    ) or 0

    merged_prs = db.scalars(
        select(PullRequest).where(
            PullRequest.repo == repo_key, PullRequest.merged_at.is_not(None)
        )
    ).all()

    avg_time_to_merge_hours: Optional[float] = None
    avg_pr_size_lines: Optional[float] = None

    if merged_prs:
        durations = [
            (pr.merged_at - pr.created_at).total_seconds() / 3600
            for pr in merged_prs
            if pr.merged_at and pr.created_at
        ]
        if durations:
            avg_time_to_merge_hours = sum(durations) / len(durations)

        sizes = [pr.additions + pr.deletions for pr in merged_prs]
        if sizes:
            avg_pr_size_lines = sum(sizes) / len(sizes)

    reviewed_prs = db.scalars(
        select(PullRequest).where(
            PullRequest.repo == repo_key, PullRequest.first_review_at.is_not(None)
        )
    ).all()

    avg_review_latency_hours: Optional[float] = None
    if reviewed_prs:
        latencies = [
            (pr.first_review_at - pr.created_at).total_seconds() / 3600
            for pr in reviewed_prs
            if pr.first_review_at and pr.created_at
        ]
        if latencies:
            avg_review_latency_hours = sum(latencies) / len(latencies)

    return PullStats(
        repo=repo_key,
        open_count=open_count,
        closed_count=closed_count,
        merged_count=merged_count,
        avg_time_to_merge_hours=avg_time_to_merge_hours,
        avg_pr_size_lines=avg_pr_size_lines,
        avg_review_latency_hours=avg_review_latency_hours,
    )
