"""HTTP 工具 + 时间解析。所有抓取器共用。"""
from __future__ import annotations

import logging
import re
import time
from datetime import datetime, timedelta, timezone

import requests
from dateutil import parser as dateparser

log = logging.getLogger("job-radar")

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

_session = requests.Session()
_session.headers.update({"User-Agent": UA, "Accept": "application/json, text/xml, */*"})

TIMEOUT = 25


def _request(method: str, url: str, retries: int = 2, **kw):
    last = None
    for i in range(retries + 1):
        try:
            r = _session.request(method, url, timeout=TIMEOUT, **kw)
            if r.status_code == 404:
                log.warning("404 %s", url)
                return None
            if r.status_code == 429:
                time.sleep(3 * (i + 1))
                continue
            r.raise_for_status()
            return r
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(1.5 * (i + 1))
    log.warning("请求失败 %s (%s)", url, last)
    return None


def get_json(url: str, **kw):
    r = _request("GET", url, **kw)
    if r is None:
        return None
    try:
        return r.json()
    except ValueError:
        log.warning("非 JSON 响应 %s", url)
        return None


def post_json(url: str, payload: dict, **kw):
    r = _request("POST", url, json=payload,
                 headers={"Content-Type": "application/json"}, **kw)
    if r is None:
        return None
    try:
        return r.json()
    except ValueError:
        return None


def get_text(url: str, **kw) -> str | None:
    r = _request("GET", url, **kw)
    return r.text if r is not None else None


# --------------------------- 时间解析 ---------------------------

def parse_dt(value) -> datetime | None:
    """尽最大努力把各种格式解析成带时区的 datetime。"""
    if value in (None, "", 0):
        return None
    try:
        if isinstance(value, (int, float)):
            ts = float(value)
            if ts > 1e12:          # 毫秒
                ts /= 1000.0
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        if isinstance(value, str):
            s = value.strip()
            if s.isdigit():
                return parse_dt(int(s))
            dt = dateparser.parse(s)
            if dt is None:
                return None
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:  # noqa: BLE001
        return None
    return None


_REL = re.compile(r"(\d+)\+?\s*(hour|day|week|month|minute)", re.I)


def parse_relative(text: str) -> datetime | None:
    """解析 Workday 的 'Posted 3 Days Ago' / 'Posted Today' 这类相对时间。"""
    if not text:
        return None
    t = text.lower()
    now = datetime.now(timezone.utc)
    if "today" in t or "just posted" in t:
        return now
    if "yesterday" in t:
        return now - timedelta(days=1)
    m = _REL.search(t)
    if not m:
        return None
    n, unit = int(m.group(1)), m.group(2)
    delta = {"minute": timedelta(minutes=n), "hour": timedelta(hours=n),
             "day": timedelta(days=n), "week": timedelta(weeks=n),
             "month": timedelta(days=30 * n)}[unit]
    return now - delta


_TAG = re.compile(r"<[^>]+>")


def strip_html(html: str, limit: int = 4000) -> str:
    if not html:
        return ""
    txt = _TAG.sub(" ", html)
    txt = re.sub(r"&nbsp;?", " ", txt)
    txt = re.sub(r"&amp;", "&", txt)
    txt = re.sub(r"\s+", " ", txt)
    return txt.strip()[:limit]
