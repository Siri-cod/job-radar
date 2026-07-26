"""SmartRecruiters 官方公开接口：api.smartrecruiters.com/v1/companies/{co}/postings"""
from __future__ import annotations
from ..models import Job
from .base import get_json, parse_dt

API = "https://api.smartrecruiters.com/v1/companies/{slug}/postings?limit=100&offset={off}"


def fetch(cfg: dict, companies: dict) -> list[Job]:
    jobs: list[Job] = []
    for slug in companies.get("smartrecruiters", []) or []:
        off = 0
        while off < 300:
            data = get_json(API.format(slug=slug, off=off))
            if not data or not data.get("content"):
                break
            for j in data["content"]:
                loc = j.get("location") or {}
                loc_s = ", ".join(x for x in [loc.get("city"), loc.get("country")] if x)
                jobs.append(Job(
                    title=j.get("name", ""),
                    company=(j.get("company") or {}).get("name") or slug,
                    location=loc_s,
                    url=f"https://jobs.smartrecruiters.com/{slug}/{j.get('id')}",
                    source="smartrecruiters",
                    posted_at=parse_dt(j.get("releasedDate") or j.get("createdOn")),
                    remote=bool(loc.get("remote")),
                    employment_type=(j.get("typeOfEmployment") or {}).get("label", "") or "",
                ))
            off += 100
            if off >= int(data.get("totalFound", 0)):
                break
    return jobs
