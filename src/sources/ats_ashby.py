"""Ashby 官方公开接口：api.ashbyhq.com/posting-api/job-board"""
from __future__ import annotations
from ..models import Job
from .base import get_json, parse_dt

API = "https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=false"


def fetch(cfg: dict, companies: dict) -> list[Job]:
    jobs: list[Job] = []
    for slug in companies.get("ashby", []) or []:
        data = get_json(API.format(slug=slug))
        if not data:
            continue
        for j in data.get("jobs", []):
            jobs.append(Job(
                title=j.get("title", ""),
                company=slug,
                location=j.get("location", "") or "",
                url=j.get("jobUrl") or j.get("applyUrl", ""),
                source="ashby",
                posted_at=parse_dt(j.get("publishedAt") or j.get("updatedAt")),
                remote=bool(j.get("isRemote")),
                description=(j.get("descriptionPlain") or "")[:4000],
                employment_type=j.get("employmentType", "") or "",
                tags=[j.get("department") or "", j.get("team") or ""],
            ))
    return jobs
