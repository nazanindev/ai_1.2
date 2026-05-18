from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.schemas import ContributorsResponse
from app.services.contributors import compute_contributor_stats

router = APIRouter(prefix="/contributors", tags=["contributors"])


@router.get("", response_model=ContributorsResponse)
async def get_contributors(
    owner: str = Query(default=None),
    repo: str = Query(default=None),
    since: datetime = Query(default=None),
    until: datetime = Query(default=None),
    db: Session = Depends(get_db),
) -> ContributorsResponse:
    resolved_owner = owner or settings.github_owner
    resolved_repo = repo or settings.github_repo

    if until is None:
        until = datetime.utcnow()
    if since is None:
        since = until - timedelta(weeks=4)

    stats = await compute_contributor_stats(
        owner=resolved_owner,
        repo=resolved_repo,
        since=since,
        until=until,
        db=db,
    )
    return ContributorsResponse(contributors=stats, total=len(stats))
