"""硬性要求识别：德语能力要求 + 最低经验年限。用正则而非关键词列表，避免误杀/漏杀。"""
from __future__ import annotations

import re

# ---------------------------------------------------------------
# 1) 明确要求德语能力
#    只匹配"把德语当作能力要求"的表述；单纯出现 "Deutschland"、
#    "Deutsche Bahn" 这类词不会触发。
# ---------------------------------------------------------------
_GERMAN_REQUIRED = [
    # 德语表述
    r"deutschkenntnis",                                   # Deutschkenntnisse
    r"(?:flie(?:ss|ß)end\w*|verhandlungssicher\w*|sehr\s+gut\w*|gut\w*)\s+deutsch",
    r"deutsch\s+in\s+wort\s+und\s+schrift",
    r"muttersprach\w*\s+deutsch",
    r"deutsch\s+auf\s+(?:mutter|c1|c2|b2)",
    r"sprachkenntnisse\s*:?\s*deutsch",
    r"deutsch\s+(?:und|&|sowie)\s+englisch",              # 两种都要
    r"(?:setzen|setzt)\s+wir\s+voraus[^.]{0,40}deutsch",
    # 英语表述
    r"fluent(?:ly)?\s+(?:in\s+)?german",
    r"german\s+(?:language\s+)?(?:skills?|proficiency|fluency|knowledge)",
    r"(?:native|business|professional|conversational|advanced)\s+(?:level\s+)?german",
    r"german\s+(?:is\s+)?(?:required|mandatory|essential|a\s+must|obligatory)",
    r"(?:required|mandatory|must\s+have)[^.]{0,40}\bgerman\b",
    r"\bgerman\b[^.]{0,25}\b(?:b2|c1|c2)\b",
    r"\b(?:b2|c1|c2)\b[^.]{0,25}\bgerman\b",
    r"speak\s+(?:fluent\s+)?german",
    r"command\s+of\s+(?:the\s+)?german",
]
# 明确说明"德语只是加分项 / 不需要德语" —— 出现这些则视为不要求
_GERMAN_OPTIONAL = [
    r"german\s+(?:is|would\s+be|are)\s+(?:a\s+)?(?:plus|bonus|nice[\s-]to[\s-]have|advantage|beneficial)",
    r"no\s+german\s+(?:is\s+)?(?:required|needed|necessary)",
    r"german\s+(?:is\s+)?not\s+(?:required|necessary|needed)",
    r"deutsch\s+(?:ist\s+)?(?:von\s+vorteil|w(?:ü|ue)nschenswert|ein\s+plus)",
    r"you\s+don'?t\s+need\s+(?:to\s+speak\s+)?german",
]

_RE_REQ = [re.compile(p, re.I) for p in _GERMAN_REQUIRED]
_RE_OPT = [re.compile(p, re.I) for p in _GERMAN_OPTIONAL]


def german_required(text: str) -> str | None:
    """返回命中的原文片段（说明为什么判定需要德语），不需要则返回 None。"""
    if not text:
        return None
    for r in _RE_OPT:                 # "德语加分" 优先，覆盖掉误判
        if r.search(text):
            return None
    for r in _RE_REQ:
        m = r.search(text)
        if m:
            s = max(0, m.start() - 30)
            return re.sub(r"\s+", " ", text[s:m.end() + 30]).strip()
    return None


# ---------------------------------------------------------------
# 2) 最低经验年限
#    "3-5 years experience" -> 3   （按下限算，通过）
#    "5+ years experience"  -> 5   （淘汰）
#    "mindestens 4 Jahre Berufserfahrung" -> 4
# ---------------------------------------------------------------
_YEARS = re.compile(
    r"(?<!\d)(\d{1,2})\s*(?:\+|plus)?\s*(?:(?:-|–|—|to|bis)\s*(\d{1,2})\s*)?"
    r"(?:\+\s*)?(?:years?|yrs?\.?|jahre?n?)"
    r"(?:[^.;\n]{0,60}?(?:experience|exp\b|erfahrung|background|working|arbeit))?",
    re.I)
_CONTEXT = re.compile(r"experience|exp\b|erfahrung|background|hands[\s-]?on|track\s+record", re.I)


def min_years_required(text: str) -> int | None:
    """抽取岗位要求的最低经验年限。抽不到返回 None。"""
    if not text:
        return None
    floors: list[int] = []
    for m in _YEARS.finditer(text):
        window = text[max(0, m.start() - 70): m.end() + 70]
        if not _CONTEXT.search(window):
            continue                          # "5 years of company history" 之类，跳过
        try:
            lo = int(m.group(1))
        except (TypeError, ValueError):
            continue
        if 0 < lo <= 20:
            floors.append(lo)
    return min(floors) if floors else None
