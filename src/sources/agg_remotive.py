"""Remotive 免费 API —— 全球远程岗位。"""
from __future__ import annotations
from ..models import Job
from .base import get_json, parse_dt, strip_html

API = "https://remotive.com/api/remote-jobs?limit=300"


def fetch(cfg: dict, companies: dict) -> list[Job]:
    data = get_json(API)
    if not data:
        return []
    out = []
    for j in data.get("jobs", []):
        out.append(Job(
            title=j.get("title", ""),
            company=j.get("company_name", ""),
            location=j.get("candidate_required_location", "") or "Remote",
            url=j.get("url", ""),
            source="remotive",
            posted_at=parse_dt(j.get("publication_date")),
            remote=True,
            description=strip_html(j.get("description", "")),
            employment_type=j.get("job_type", "") or "",
            tags=j.get("tags") or [],
        ))
    return out
