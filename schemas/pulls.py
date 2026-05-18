from typing import Optional
from pydantic import BaseModel


class PullStats(BaseModel):
    repo: str
    open_count: int
    closed_count: int
    merged_count: int
    avg_time_to_merge_hours: Optional[float]
    avg_pr_size_lines: Optional[float]
    avg_review_latency_hours: Optional[float]
