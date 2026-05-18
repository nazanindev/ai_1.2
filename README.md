# GitHub Metrics API

A FastAPI service that aggregates GitHub repository statistics: PR throughput, commit frequency, and review latency by contributor.

Built with [ai-flow](https://github.com/nazanindev/ai-flow) using a coordinator + four parallel executor agents.

---

## Overview

| Domain | Responsibility |
|--------|---------------|
| **Repos** | List tracked repositories, add/remove repos |
| **PRs** | PR stats: open/merged counts, cycle time, size distribution |
| **Contributor Stats** | Per-author commit frequency, review latency, PR acceptance rate |
| **Webhook Ingestion** | Receive GitHub webhook events and persist to the database |

---

## Endpoints

### Repositories
```
GET  /repos              — list all tracked repos
POST /repos              — add a repo to track
DELETE /repos/{owner}/{repo}  — stop tracking a repo
```

### Pull Requests
```
GET /repos/{owner}/{repo}/prs          — PR list with metadata
GET /repos/{owner}/{repo}/prs/stats    — aggregated PR stats
  ?since=YYYY-MM-DD
  ?until=YYYY-MM-DD
```

### Contributor Stats
```
GET /repos/{owner}/{repo}/contributors            — contributor list
GET /repos/{owner}/{repo}/contributors/{login}   — per-contributor breakdown
  Response includes: commit_count, prs_opened, prs_merged,
                     avg_review_latency_hours, avg_pr_cycle_time_hours
```

### Webhooks
```
POST /webhooks/github    — GitHub webhook receiver (push, pull_request, pull_request_review)
```

---

## Stack

- **FastAPI** — API framework
- **SQLite / SQLAlchemy** — local persistence (swap to Postgres for production)
- **PyGitHub** — GitHub REST API client
- **Uvicorn** — ASGI server

---

## Quickstart

```bash
pip install -r requirements.txt

export GITHUB_TOKEN=ghp_...
export WEBHOOK_SECRET=your-webhook-secret   # optional

uvicorn main:app --reload
```

API docs available at `http://localhost:8000/docs`.

---

## Harness Issues Surfaced This Run

Two issues were identified during the multi-agent build that need fixes in the coordinator template.

### 1. Coordinator partitioning — file ownership conflicts

All four executor agents independently created `main.py`, `database.py`, and `requirements.txt`. At merge time this produced conflicts across every shared file.

**Fix needed in the spawn plan:** assign explicit file ownership per agent before spawning. Example partition:

| Agent | Owns |
|-------|------|
| repos-agent | `routers/repos.py`, `models/repo.py` |
| prs-agent | `routers/prs.py`, `models/pr.py` |
| contributors-agent | `routers/contributors.py`, `models/contributor.py` |
| webhooks-agent | `routers/webhooks.py`, `ingest/handler.py` |
| coordinator | `main.py`, `database.py`, `requirements.txt`, `schemas/` |

The coordinator should create the shared scaffolding first, then spawn executors with a strict instruction: *do not create or modify files outside your owned paths.*

### 2. Bash allowlist — unnecessary blocks

The harness blocked common shell operations during the build:

| Blocked command | Why it's needed |
|-----------------|-----------------|
| `cd` | Navigating into subdirectories for scoped installs |
| `for` (bash loop) | Batch operations over file lists |
| `pip3` | Installing Python dependencies |

**Fix:** add `cd`, `for`, and `pip3` to the project-level Bash allowlist in `.claude/settings.json`:

```json
{
  "permissions": {
    "allow": [
      "Bash(cd:*)",
      "Bash(for:*)",
      "Bash(pip3:*)"
    ]
  }
}
```
