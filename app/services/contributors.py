from collections import defaultdict
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy.orm import Session

from app import github_client as gh
from app.models import Contributor
from app.schemas import ContributorStats


def _week_start(dt: datetime) -> datetime:
    """Return the Monday of the week containing dt (UTC)."""
    return (dt - timedelta(days=dt.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)


def _parse_dt(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


async def compute_contributor_stats(
    owner: str,
    repo: str,
    since: datetime,
    until: datetime,
    db: Session,
    client: httpx.AsyncClient | None = None,
) -> list[ContributorStats]:
    # --- fetch raw data ---
    raw_commits = await gh.fetch_commits(owner, repo, since, until, client=client)
    raw_prs = await gh.fetch_pull_requests(owner, repo, state="all", client=client)

    # --- aggregate commits ---
    # keyed by (login, week_start_date)
    commit_counts: dict[tuple[str, datetime], int] = defaultdict(int)
    lines_added: dict[tuple[str, datetime], int] = defaultdict(int)
    lines_deleted: dict[tuple[str, datetime], int] = defaultdict(int)

    for c in raw_commits:
        author = c.get("author") or {}
        login = author.get("login")
        if not login:
            login = (c.get("commit") or {}).get("author", {}).get("name", "unknown")
        committed_at_str = (c.get("commit") or {}).get("author", {}).get("date", "")
        if not committed_at_str:
            continue
        committed_at = _parse_dt(committed_at_str)
        week = _week_start(committed_at)
        key = (login, week)
        commit_counts[key] += 1

        # Fetch per-commit line stats
        detail = await gh.fetch_commit_diff(owner, repo, c["sha"], client=client)
        stats = detail.get("stats") or {}
        lines_added[key] += stats.get("additions", 0)
        lines_deleted[key] += stats.get("deletions", 0)

    # --- aggregate PRs authored ---
    prs_authored: dict[tuple[str, datetime], int] = defaultdict(int)
    # keyed by pr number → (login, week)
    pr_meta: dict[int, tuple[str, datetime]] = {}

    for pr in raw_prs:
        user = pr.get("user") or {}
        login = user.get("login", "unknown")
        created_str = pr.get("created_at", "")
        if not created_str:
            continue
        created_at = _parse_dt(created_str)
        if not (since <= created_at.replace(tzinfo=None) <= until):
            continue
        week = _week_start(created_at)
        key = (login, week)
        prs_authored[key] += 1
        pr_meta[pr["number"]] = (login, week, created_at)  # type: ignore[assignment]

    # --- aggregate PR reviews ---
    prs_reviewed: dict[tuple[str, datetime], int] = defaultdict(int)
    turnaround_totals: dict[tuple[str, datetime], float] = defaultdict(float)
    turnaround_counts: dict[tuple[str, datetime], int] = defaultdict(int)

    for pr in raw_prs:
        pr_number = pr["number"]
        created_str = pr.get("created_at", "")
        if not created_str:
            continue
        pr_created_at = _parse_dt(created_str)

        reviews = await gh.fetch_pr_reviews(owner, repo, pr_number, client=client)
        seen_reviewers: set[str] = set()
        first_review_at: datetime | None = None

        for review in reviews:
            reviewer = (review.get("user") or {}).get("login", "unknown")
            submitted_str = review.get("submitted_at", "")
            if not submitted_str:
                continue
            submitted_at = _parse_dt(submitted_str)
            week = _week_start(submitted_at)
            key = (reviewer, week)

            if reviewer not in seen_reviewers:
                prs_reviewed[key] += 1
                seen_reviewers.add(reviewer)

            if first_review_at is None or submitted_at < first_review_at:
                first_review_at = submitted_at

        if first_review_at is not None:
            turnaround_hours = (first_review_at - pr_created_at).total_seconds() / 3600
            # attribute turnaround to the PR author's week bucket
            pr_author = (pr.get("user") or {}).get("login", "unknown")
            pr_created_week = _week_start(pr_created_at)
            author_key = (pr_author, pr_created_week)
            turnaround_totals[author_key] += turnaround_hours
            turnaround_counts[author_key] += 1

    # --- collect all actor/week keys ---
    all_keys: set[tuple[str, datetime]] = (
        set(commit_counts)
        | set(prs_authored)
        | set(prs_reviewed)
    )

    results: list[ContributorStats] = []

    for login, week in all_keys:
        key = (login, week)
        commits = commit_counts[key]
        weeks_in_range = max(((until - since).days / 7), 1)
        commit_freq = commits / weeks_in_range

        ta_count = turnaround_counts.get(key, 0)
        avg_turnaround = (
            turnaround_totals[key] / ta_count if ta_count > 0 else 0.0
        )

        # upsert into DB
        week_date = week.date() if hasattr(week, "date") else week
        db_row = (
            db.query(Contributor)
            .filter_by(login=login, owner=owner, repo=repo, week_start=week_date)
            .first()
        )
        if db_row is None:
            db_row = Contributor(login=login, owner=owner, repo=repo, week_start=week_date)
            db.add(db_row)

        db_row.commits = commits
        db_row.commit_frequency = commit_freq
        db_row.prs_authored = prs_authored.get(key, 0)
        db_row.prs_reviewed = prs_reviewed.get(key, 0)
        db_row.avg_review_turnaround_hours = avg_turnaround
        db_row.lines_added = lines_added.get(key, 0)
        db_row.lines_deleted = lines_deleted.get(key, 0)

        results.append(
            ContributorStats(
                login=login,
                owner=owner,
                repo=repo,
                week_start=week_date,
                commits=commits,
                commit_frequency=round(commit_freq, 4),
                prs_authored=prs_authored.get(key, 0),
                prs_reviewed=prs_reviewed.get(key, 0),
                avg_review_turnaround_hours=round(avg_turnaround, 4),
                lines_added=lines_added.get(key, 0),
                lines_deleted=lines_deleted.get(key, 0),
            )
        )

    db.commit()
    return results
