from datetime import date

from pydantic import BaseModel


class ContributorStats(BaseModel):
    login: str
    owner: str
    repo: str
    week_start: date
    commits: int
    commit_frequency: float
    prs_authored: int
    prs_reviewed: int
    avg_review_turnaround_hours: float
    lines_added: int
    lines_deleted: int

    model_config = {"from_attributes": True}


class ContributorsResponse(BaseModel):
    contributors: list[ContributorStats]
    total: int
