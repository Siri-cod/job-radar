"""RemoteOK 免费 API —— 全球远程岗位。首元素是 legal notice，需跳过。"""
from __future__ import annotations
from ..models import Job
from .base import get_json, parse_dt, strip_html

API = "https://remoteok.com/api"


def fetch(cfg: dict, companies: dict) -> list[Job]:
    data = get_json(API)
    if not isinstance(data, list):
        return []
    out = []
    for j in data:
        if not isinstance(j, dict) or not j.get("position"):
            continue
        out.append(Job(
            title=j.get("position", ""),
            company=j.get("company", ""),
            location=j.get("location") or "Remote",
            url=j.get("url") or j.get("apply_url", ""),
            source="remoteok",
            posted_at=parse_dt(j.get("date") or j.get("epoch")),
            remote=True,
            description=strip_html(j.get("description", "")),
            tags=j.get("tags") or [],
        ))
    return out
