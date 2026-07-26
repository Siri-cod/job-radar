from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())


@dataclass
class Job:
    """统一后的岗位对象。所有数据源都必须产出这个结构。"""

    title: str
    company: str
    location: str
    url: str                      # 直接投递/详情页链接
    source: str                   # 数据源名
    posted_at: datetime | None = None
    remote: bool = False
    description: str = ""
    tags: list[str] = field(default_factory=list)
    employment_type: str = ""

    # 运行时填充
    score: int = 0
    reasons: list[str] = field(default_factory=list)
    first_seen: str = ""
    is_new: bool = False
    reject_reason: str = ""

    @property
    def fingerprint(self) -> str:
        """跨数据源去重：公司+标题+地点归一化后哈希。"""
        key = f"{_norm(self.company)}|{_norm(self.title)}|{_norm(self.location)[:24]}"
        return hashlib.sha1(key.encode()).hexdigest()[:16]

    @property
    def age_hours(self) -> float:
        if not self.posted_at:
            return 9999.0
        now = datetime.now(timezone.utc)
        return (now - self.posted_at).total_seconds() / 3600

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["posted_at"] = self.posted_at.isoformat() if self.posted_at else None
        d["fingerprint"] = self.fingerprint
        d["age_hours"] = round(self.age_hours, 1)
        return d
