"""Greenhouse 官方公开接口：boards-api.greenhouse.io"""
from __future__ import annotations
from ..models import Job
from .base import get_json, parse_dt, strip_html

API = "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"


def fetch(cfg: dict, companies: dict) -> list[Job]:
    jobs: list[Job] = []
    for slug in companies.get("greenhouse", []) or []:
        data = get_json(API.format(slug=slug))
        if not data:
            continue
        for j in data.get("jobs", []):
            loc = (j.get("location") or {}).get("name", "")
            jobs.append(Job(
                title=j.get("title", ""),
                company=slug,
                location=loc,
                url=j.get("absolute_url", ""),
                source="greenhouse",
                posted_at=parse_dt(j.get("first_published") or j.get("updated_at")),
                remote="remote" in loc.lower(),
                description=strip_html(j.get("content", "")),
            ))
    return jobs
