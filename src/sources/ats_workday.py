"""Workday CXS 接口（大厂常用）。postedOn 是相对时间文本，需要换算。"""
from __future__ import annotations

from ..models import Job
from .base import post_json, parse_relative, parse_dt

PAGE = 20


def fetch(cfg: dict, companies: dict) -> list[Job]:
    jobs: list[Job] = []
    for entry in companies.get("workday", []) or []:
        host, tenant, site = entry.get("host"), entry.get("tenant"), entry.get("site")
        if not (host and tenant and site):
            continue
        url = f"https://{host}/wday/cxs/{tenant}/{site}/jobs"
        for offset in range(0, 100, PAGE):
            data = post_json(url, {"appliedFacets": {}, "limit": PAGE,
                                   "offset": offset, "searchText": ""})
            if not data or not data.get("jobPostings"):
                break
            for j in data["jobPostings"]:
                path = j.get("externalPath", "")
                jobs.append(Job(
                    title=j.get("title", ""),
                    company=tenant,
                    location=j.get("locationsText", "") or "",
                    url=f"https://{host}/{site}{path}",
                    source="workday",
                    posted_at=parse_relative(j.get("postedOn", "")) or parse_dt(j.get("startDate")),
                    remote="remote" in (j.get("locationsText") or "").lower(),
                    description=" ".join(j.get("bulletFields") or []),
                ))
            if len(data["jobPostings"]) < PAGE:
                break
    return jobs
