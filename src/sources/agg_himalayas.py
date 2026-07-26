"""Himalayas 免费 API —— 全球远程岗位。"""
from __future__ import annotations
from ..models import Job
from .base import get_json, parse_dt, strip_html

API = "https://himalayas.app/jobs/api?limit=200"


def fetch(cfg: dict, companies: dict) -> list[Job]:
    data = get_json(API)
    if not data:
        return []
    out = []
    for j in data.get("jobs", []):
        locs = j.get("locationRestrictions") or []
        out.append(Job(
            title=j.get("title", ""),
            company=j.get("companyName", ""),
            location=", ".join(locs) if locs else "Remote (Worldwide)",
            url=j.get("applicationLink") or j.get("guid", ""),
            source="himalayas",
            posted_at=parse_dt(j.get("pubDate")),
            remote=True,
            description=strip_html(j.get("description") or j.get("excerpt", "")),
            employment_type=", ".join(j.get("employmentType") or []) if isinstance(j.get("employmentType"), list) else (j.get("employmentType") or ""),
            tags=j.get("categories") or [],
        ))
    return out
