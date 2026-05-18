from typing import Any
import httpx


class GitHubClient:
    BASE_URL = "https://api.github.com"

    def __init__(self, token: str = ""):
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self._client = httpx.AsyncClient(base_url=self.BASE_URL, headers=headers)

    async def __aenter__(self) -> "GitHubClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self._client.aclose()

    async def get_pulls(self, owner: str, repo: str) -> list[dict]:
        pulls: list[dict] = []
        page = 1
        while True:
            resp = await self._client.get(
                f"/repos/{owner}/{repo}/pulls",
                params={"state": "all", "per_page": 100, "page": page},
            )
            resp.raise_for_status()
            batch = resp.json()
            if not batch:
                break
            pulls.extend(batch)
            page += 1
        return pulls

    async def get_reviews(self, owner: str, repo: str, pull_number: int) -> list[dict]:
        resp = await self._client.get(f"/repos/{owner}/{repo}/pulls/{pull_number}/reviews")
        resp.raise_for_status()
        return resp.json()
