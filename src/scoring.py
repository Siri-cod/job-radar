"""精准筛选核心：硬排除 + 加权打分。"""
from __future__ import annotations

from .models import Job
from .requirements_filter import german_required, min_years_required

REJECT = "__reject__"


def _hit(text: str, needles) -> list[str]:
    t = text.lower()
    return [n for n in (needles or []) if str(n).lower() in t]


def evaluate(job: Job, cfg: dict) -> bool:
    """就地填充 job.score / job.reasons。返回 False 表示该岗位被淘汰。"""
    p = cfg.get("profile") or {}
    loc_cfg = cfg.get("locations") or {}
    f = cfg.get("filters") or {}

    title = (job.title or "").lower()
    body = f"{job.title} {job.description} {' '.join(job.tags)} {job.employment_type}".lower()
    location = (job.location or "").lower()

    score = 0
    reasons: list[str] = []

    # 1) 标题必须命中目标职位
    hits = _hit(title, p.get("titles_any"))
    if p.get("titles_any") and not hits:
        return False
    score += 10 + 2 * (len(hits) - 1 if hits else 0)
    if hits:
        reasons.append("职位匹配: " + ", ".join(hits[:3]))

    # 2) 必须同时包含
    for must in p.get("titles_all") or []:
        if str(must).lower() not in title:
            return False

    # 3) 标题硬排除（职级不符 / 实习等）
    bad = _hit(title, p.get("titles_exclude"))
    if bad:
        return False

    # 4) 正文硬排除
    if _hit(body, p.get("keywords_exclude")):
        return False

    # 4.5) 硬性要求：德语能力 / 经验年限
    #      注意：检查始终对 标题+描述 全文执行，不因描述短而跳过。
    #      描述长度只用来决定"抓不到正文时是否保留"以及是否给加分。
    req = cfg.get("requirements") or {}
    desc = (job.description or "").strip()
    has_desc = len(desc) >= 60
    raw_text = f"{job.title}\n{desc}"

    if not has_desc and not req.get("keep_when_description_missing", True):
        return False

    if req.get("exclude_german_required", False):
        hit = german_required(raw_text)
        if hit:
            job.reject_reason = f"要求德语: {hit[:70]}"
            return False
        if has_desc:
            score += 4
            reasons.append("未要求德语")

    max_y = req.get("max_years_experience")
    if max_y is not None:
        yrs = min_years_required(raw_text)
        if yrs is not None:
            if yrs > int(max_y):
                job.reject_reason = f"要求 {yrs} 年经验（上限 {max_y}）"
                return False
            score += 4
            reasons.append(f"经验要求 {yrs} 年")
        elif has_desc:
            score += 2
            reasons.append("未标明经验年限")

    # 5) 地点
    remote_ok = bool(loc_cfg.get("allow_remote", True))
    country_hit = _hit(location, loc_cfg.get("countries"))
    city_hit = _hit(location, loc_cfg.get("cities"))
    is_remote = job.remote or "remote" in location or "anywhere" in location

    if city_hit:
        score += 8
        reasons.append("目标城市: " + city_hit[0])
    elif country_hit:
        score += 6
        reasons.append("目标国家: " + country_hit[0])
    elif is_remote and remote_ok:
        if str(loc_cfg.get("remote_scope", "global")).lower() == "europe" \
                and not _hit(location, ["europe", "emea", "eu", "germany", "worldwide"]):
            return False
        score += 5
        reasons.append("远程岗位")
    else:
        return False   # 地点完全不符，直接淘汰

    # 6) 技能/条件关键词加分
    for kw, w in (p.get("keywords_boost") or {}).items():
        if str(kw).lower() in body:
            score += int(w)
            reasons.append(f"+{w} {kw}")

    # 7) 新鲜度加分：越新分越高
    age = job.age_hours
    if age <= 24:
        score += 10
        reasons.append("24 小时内发布")
    elif age <= 72:
        score += 6
    elif age <= 168:
        score += 3

    # 8) 官网直连比聚合平台更可信
    if job.source in {"greenhouse", "lever", "ashby", "smartrecruiters",
                      "recruitee", "personio", "workday"}:
        score += 3
        reasons.append("公司官网直发")

    job.score = score
    job.reasons = reasons
    return score >= int(f.get("min_score", 0))
