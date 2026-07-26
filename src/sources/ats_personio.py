"""Personio 官方 XML feed（德国中小公司大量使用）：{co}.jobs.personio.de/xml"""
from __future__ import annotations

import xml.etree.ElementTree as ET

from ..models import Job
from .base import get_text, parse_dt, strip_html

API = "https://{slug}.jobs.personio.de/xml"


def _txt(node, tag) -> str:
    el = node.find(tag)
    return (el.text or "").strip() if el is not None and el.text else ""


def fetch(cfg: dict, companies: dict) -> list[Job]:
    jobs: list[Job] = []
    for slug in companies.get("personio", []) or []:
        xml = get_text(API.format(slug=slug))
        if not xml:
            continue
        try:
            root = ET.fromstring(xml.encode("utf-8"))
        except ET.ParseError:
            continue
        for pos in root.iter("position"):
            jid = _txt(pos, "id")
            office = _txt(pos, "office")
            desc = " ".join(strip_html(ET.tostring(d, encoding="unicode"))
                            for d in pos.iter("jobDescription"))
            jobs.append(Job(
                title=_txt(pos, "name"),
                company=_txt(pos, "subcompany") or slug,
                location=office,
                url=f"https://{slug}.jobs.personio.de/job/{jid}",
                source="personio",
                posted_at=parse_dt(_txt(pos, "createdAt")),
                remote="remote" in (office + desc[:300]).lower(),
                description=desc[:4000],
                employment_type=_txt(pos, "employmentType"),
                tags=[t for t in [_txt(pos, "department"), _txt(pos, "seniority")] if t],
            ))
    return jobs
