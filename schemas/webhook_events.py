from datetime import datetime

from pydantic import BaseModel


class GithubUser(BaseModel):
    login: str
    id: int


class GithubRepo(BaseModel):
    id: int
    full_name: str
    html_url: str


class PullRequestPayload(BaseModel):
    id: int
    number: int
    title: str
    state: str
    html_url: str
    user: GithubUser
    created_at: datetime
    updated_at: datetime
    merged_at: datetime | None = None


class PullRequestEvent(BaseModel):
    action: str
    pull_request: PullRequestPayload
    repository: GithubRepo
    sender: GithubUser


class Commit(BaseModel):
    id: str
    message: str
    author: dict


class PushEventPayload(BaseModel):
    ref: str
    before: str
    after: str
    repository: GithubRepo
    pusher: GithubUser
    commits: list[Commit] = []


class ReviewPayload(BaseModel):
    id: int
    state: str
    body: str | None = None
    user: GithubUser
    submitted_at: datetime | None = None
    html_url: str


class PullRequestReviewEvent(BaseModel):
    action: str
    review: ReviewPayload
    pull_request: PullRequestPayload
    repository: GithubRepo
    sender: GithubUser
