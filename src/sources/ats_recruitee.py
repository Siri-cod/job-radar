"""Recruitee 官方公开接口：{co}.recruitee.com/api/offers"""
from __future__ import annotations
from ..models import Job
from .base import get_json, parse_dt, strip_html

API = "https://{slug}.recruitee.com/api/offers/"


def fetch(cfg: dict, companies: dict) -> list[Job]:
    jobs: list[Job] = []
    for slug in companies.get("recruitee", []) or []:
        data = get_json(API.format(slug=slug))
        if not data:
            continue
        for j in data.get("offers", []):
            loc = ", ".join(x for x in [j.get("city"), j.get("country")] if x) or j.get("location", "")
            jobs.append(Job(
                title=j.get("title", ""),
                company=slug,
                location=loc or "",
                url=j.get("careers_url") or j.get("careers_apply_url", ""),
                source="recruitee",
                posted_at=parse_dt(j.get("published_at") or j.get("created_at")),
                remote=bool(j.get("remote")),
                description=strip_html(j.get("description", "")),
                employment_type=j.get("employment_type_code", "") or "",
                tags=j.get("tags") or [],
            ))
    return jobs
