from datetime import datetime
from typing import Any

import httpx

from app.config import settings

GITHUB_API = "https://api.github.com"


def _headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"
    return headers


async def fetch_commits(
    owner: str,
    repo: str,
    since: datetime,
    until: datetime,
    client: httpx.AsyncClient | None = None,
) -> list[dict[str, Any]]:
    url = f"{GITHUB_API}/repos/{owner}/{repo}/commits"
    params = {
        "since": since.isoformat() + "Z",
        "until": until.isoformat() + "Z",
        "per_page": 100,
    }
    results: list[dict[str, Any]] = []
    _client = client or httpx.AsyncClient(headers=_headers())
    try:
        while url:
            resp = await _client.get(url, params=params, headers=_headers())
            resp.raise_for_status()
            results.extend(resp.json())
            url = resp.links.get("next", {}).get("url")
            params = {}  # pagination link already includes params
    finally:
        if client is None:
            await _client.aclose()
    return results


async def fetch_pull_requests(
    owner: str,
    repo: str,
    state: str = "all",
    client: httpx.AsyncClient | None = None,
) -> list[dict[str, Any]]:
    url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls"
    params = {"state": state, "per_page": 100}
    results: list[dict[str, Any]] = []
    _client = client or httpx.AsyncClient(headers=_headers())
    try:
        while url:
            resp = await _client.get(url, params=params, headers=_headers())
            resp.raise_for_status()
            results.extend(resp.json())
            url = resp.links.get("next", {}).get("url")
            params = {}
    finally:
        if client is None:
            await _client.aclose()
    return results


async def fetch_pr_reviews(
    owner: str,
    repo: str,
    pull_number: int,
    client: httpx.AsyncClient | None = None,
) -> list[dict[str, Any]]:
    url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pull_number}/reviews"
    params = {"per_page": 100}
    results: list[dict[str, Any]] = []
    _client = client or httpx.AsyncClient(headers=_headers())
    try:
        while url:
            resp = await _client.get(url, params=params, headers=_headers())
            resp.raise_for_status()
            results.extend(resp.json())
            url = resp.links.get("next", {}).get("url")
            params = {}
    finally:
        if client is None:
            await _client.aclose()
    return results


async def fetch_commit_diff(
    owner: str,
    repo: str,
    sha: str,
    client: httpx.AsyncClient | None = None,
) -> dict[str, Any]:
    url = f"{GITHUB_API}/repos/{owner}/{repo}/commits/{sha}"
    _client = client or httpx.AsyncClient(headers=_headers())
    try:
        resp = await _client.get(url, headers=_headers())
        resp.raise_for_status()
        return resp.json()
    finally:
        if client is None:
            await _client.aclose()
