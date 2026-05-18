from datetime import datetime
from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class PullRequest(Base):
    __tablename__ = "pull_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    repo: Mapped[str] = mapped_column(String, index=True)
    number: Mapped[int] = mapped_column(Integer)
    state: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    merged_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    additions: Mapped[int] = mapped_column(Integer, default=0)
    deletions: Mapped[int] = mapped_column(Integer, default=0)
    first_review_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
