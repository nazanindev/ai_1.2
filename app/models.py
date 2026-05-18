from datetime import date

from sqlalchemy import Date, Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Contributor(Base):
    __tablename__ = "contributors"
    __table_args__ = (UniqueConstraint("login", "owner", "repo", "week_start", name="uq_contributor_week"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    login: Mapped[str] = mapped_column(String, nullable=False, index=True)
    owner: Mapped[str] = mapped_column(String, nullable=False)
    repo: Mapped[str] = mapped_column(String, nullable=False)
    week_start: Mapped[date] = mapped_column(Date, nullable=False)

    commits: Mapped[int] = mapped_column(Integer, default=0)
    commit_frequency: Mapped[float] = mapped_column(Float, default=0.0)  # commits per week
    prs_authored: Mapped[int] = mapped_column(Integer, default=0)
    prs_reviewed: Mapped[int] = mapped_column(Integer, default=0)
    avg_review_turnaround_hours: Mapped[float] = mapped_column(Float, default=0.0)
    lines_added: Mapped[int] = mapped_column(Integer, default=0)
    lines_deleted: Mapped[int] = mapped_column(Integer, default=0)
