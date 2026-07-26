"""德国联邦劳工局（Bundesagentur für Arbeit）官方公开 API —— 德国岗位覆盖最全。"""
from __future__ import annotations

from ..models import Job
from .base import get_json, parse_dt

API = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobs"
HEADERS = {"X-API-Key": "jobboerse-jobsuche"}
DETAIL = "https://www.arbeitsagentur.de/jobsuche/jobdetail/{hash}"


def fetch(cfg: dict, companies: dict) -> list[Job]:
    scfg = (cfg.get("sources") or {}).get("arbeitsagentur") or {}
    queries = scfg.get("queries") or ["Data Analyst"]
    wo = scfg.get("wo", "Deutschland")
    umkreis = scfg.get("umkreis", 200)
    days = int((cfg.get("filters") or {}).get("freshness_days", 7))

    jobs: list[Job] = []
    for q in queries:
        for page in (1, 2):
            params = {"was": q, "wo": wo, "umkreis": umkreis, "size": 100,
                      "page": page, "veroeffentlichtseit": min(days, 100)}
            data = get_json(API, params=params, headers=HEADERS)
            if not data:
                break
            items = data.get("stellenangebote") or []
            for j in items:
                ort = j.get("arbeitsort") or {}
                loc = ", ".join(x for x in [ort.get("ort"), ort.get("region"),
                                            (ort.get("land") or "Deutschland")] if x)
                h = j.get("hashId") or ""
                jobs.append(Job(
                    title=j.get("titel") or j.get("beruf", ""),
                    company=j.get("arbeitgeber", ""),
                    location=loc,
                    url=j.get("externeUrl") or DETAIL.format(hash=h),
                    source="arbeitsagentur",
                    posted_at=parse_dt(j.get("aktuelleVeroeffentlichungsdatum")
                                       or j.get("eintrittsdatum")),
                    description=j.get("beruf", ""),
                ))
            if len(items) < 100:
                break
    return jobs
