"""Lever 官方公开接口：api.lever.co/v0/postings"""
from __future__ import annotations
from ..models import Job
from .base import get_json, parse_dt

API = "https://api.lever.co/v0/postings/{slug}?mode=json"


def fetch(cfg: dict, companies: dict) -> list[Job]:
    jobs: list[Job] = []
    for slug in companies.get("lever", []) or []:
        data = get_json(API.format(slug=slug))
        if not isinstance(data, list):
            continue
        for j in data:
            cat = j.get("categories") or {}
            loc = cat.get("location", "") or ""
            jobs.append(Job(
                title=j.get("text", ""),
                company=slug,
                location=loc,
                url=j.get("hostedUrl") or j.get("applyUrl", ""),
                source="lever",
                posted_at=parse_dt(j.get("createdAt")),
                remote="remote" in (loc + str(cat.get("commitment", ""))).lower(),
                description=(j.get("descriptionPlain") or "")[:4000],
                employment_type=cat.get("commitment", "") or "",
                tags=[v for v in [cat.get("team"), cat.get("department")] if v],
            ))
    return jobs
