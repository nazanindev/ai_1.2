from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Repository(Base):
    __tablename__ = "repositories"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    html_url: Mapped[str] = mapped_column(String(512), nullable=False)

    pull_requests: Mapped[list["PullRequest"]] = relationship(back_populates="repository")
    push_events: Mapped[list["PushEvent"]] = relationship(back_populates="repository")


class PullRequest(Base):
    __tablename__ = "pull_requests"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    repository_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("repositories.id"), nullable=False)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    author: Mapped[str] = mapped_column(String(255), nullable=False)
    html_url: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    merged_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    repository: Mapped["Repository"] = relationship(back_populates="pull_requests")
    reviews: Mapped[list["PullRequestReview"]] = relationship(back_populates="pull_request")


class PushEvent(Base):
    __tablename__ = "push_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    repository_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("repositories.id"), nullable=False)
    ref: Mapped[str] = mapped_column(String(255), nullable=False)
    before: Mapped[str] = mapped_column(String(40), nullable=False)
    after: Mapped[str] = mapped_column(String(40), nullable=False)
    pusher: Mapped[str] = mapped_column(String(255), nullable=False)
    commit_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    received_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    repository: Mapped["Repository"] = relationship(back_populates="push_events")


class PullRequestReview(Base):
    __tablename__ = "pull_request_reviews"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    pull_request_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("pull_requests.id"), nullable=False)
    state: Mapped[str] = mapped_column(String(64), nullable=False)
    author: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    html_url: Mapped[str] = mapped_column(String(512), nullable=False)

    pull_request: Mapped["PullRequest"] = relationship(back_populates="reviews")
