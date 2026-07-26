"""Arbeitnow 免费公开 API —— 德国岗位为主，带 visa sponsorship 标记。"""
from __future__ import annotations

from ..models import Job
from .base import get_json, parse_dt, strip_html

API = "https://www.arbeitnow.com/api/job-board-api"
MAX_PAGES = 5


def fetch(cfg: dict, companies: dict) -> list[Job]:
    jobs: list[Job] = []
    url = API
    for _ in range(MAX_PAGES):
        data = get_json(url)
        if not data:
            break
        for j in data.get("data", []):
            jobs.append(Job(
                title=j.get("title", ""),
                company=j.get("company_name", ""),
                location=j.get("location", "") or "Germany",
                url=j.get("url", ""),
                source="arbeitnow",
                posted_at=parse_dt(j.get("created_at")),
                remote=bool(j.get("remote")),
                description=strip_html(j.get("description", "")),
                tags=(j.get("tags") or []) + (j.get("job_types") or []),
            ))
        nxt = (data.get("links") or {}).get("next")
        if not nxt:
            break
        url = nxt
    return jobs
