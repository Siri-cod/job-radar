"""入口：抓取 -> 新鲜度过滤 -> 打分 -> 去重 -> 看板 + 邮件。

用法:
    python -m src.main              # 正常运行
    python -m src.main --dry-run    # 不发邮件
    python -m src.main --only greenhouse,arbeitnow
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import yaml

from . import notify
from .render import render_html
from .scoring import evaluate
from .sources import REGISTRY
from .store import Store

ROOT = Path(__file__).resolve().parent.parent
logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("job-radar")


def load_yaml(name: str) -> dict:
    p = ROOT / name
    if not p.exists():
        return {}
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}


def collect(cfg: dict, companies: dict, only: set[str] | None) -> list:
    src_cfg = cfg.get("sources") or {}
    active = [n for n, fn in REGISTRY.items()
              if (src_cfg.get(n) or {}).get("enabled", False)
              and (not only or n in only)]
    jobs: list = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(REGISTRY[n], cfg, companies): n for n in active}
        for fut in as_completed(futs):
            name = futs[fut]
            try:
                got = fut.result() or []
                log.info("  %-16s %4d 条", name, len(got))
                jobs += got
            except Exception as e:  # noqa: BLE001
                log.warning("  %-16s 失败: %s", name, e)
    return jobs


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="不发送邮件")
    ap.add_argument("--only", default="", help="只跑指定数据源，逗号分隔")
    args = ap.parse_args(argv)

    cfg = load_yaml("config.yaml")
    companies = load_yaml("companies.yaml")
    filters = cfg.get("filters") or {}
    only = {s.strip() for s in args.only.split(",") if s.strip()} or None

    log.info("抓取数据源…")
    raw = collect(cfg, companies, only)
    log.info("原始岗位 %d 条", len(raw))

    # 新鲜度过滤
    max_h = float(filters.get("freshness_days", 7)) * 24
    fresh = [j for j in raw if j.age_hours <= max_h]
    log.info("新鲜度过滤后 %d 条（%s 天内）", len(fresh), filters.get("freshness_days", 7))

    # 打分 + 精准筛选
    matched, rejected = [], []
    for j in fresh:
        (matched if evaluate(j, cfg) else rejected).append(j)
    log.info("精准匹配 %d 条", len(matched))
    hard = [j for j in rejected if j.reject_reason]
    if hard:
        log.info("因硬性条件淘汰 %d 条（德语要求/经验年限，明细见 data/rejected.json）", len(hard))

    # 去重（同一岗位在多个平台重复出现时只保留分数最高的）
    best: dict[str, object] = {}
    for j in matched:
        cur = best.get(j.fingerprint)
        if cur is None or j.score > cur.score:
            best[j.fingerprint] = j
    uniq = sorted(best.values(), key=lambda j: (-j.score, j.age_hours))
    uniq = uniq[: int(filters.get("max_per_run", 400))]
    log.info("去重后 %d 条", len(uniq))

    # 标记新岗位 + 挑出需要提醒的
    store = Store(ROOT / "data" / "seen.sqlite")
    alert_h = float(filters.get("alert_window_hours", 24))
    to_alert = []
    for j in uniq:
        is_new = store.is_new(j)
        j.is_new = is_new
        if is_new and j.age_hours <= alert_h and not store.was_notified(j.fingerprint):
            to_alert.append(j)
    store.commit()

    # 输出
    out = render_html(uniq, cfg, ROOT / "docs" / "index.html")
    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "data" / "jobs.json").write_text(
        json.dumps({"generated_at": datetime.now(timezone.utc).isoformat(),
                    "count": len(uniq),
                    "jobs": [j.to_dict() for j in uniq]},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    # 淘汰清单：用来诊断"是不是过滤太狠了"
    (ROOT / "data" / "rejected.json").write_text(
        json.dumps([{"title": j.title, "company": j.company, "url": j.url,
                     "source": j.source, "reason": j.reject_reason}
                    for j in hard[:300]], ensure_ascii=False, indent=1),
        encoding="utf-8")
    log.info("看板已生成: %s", out)

    # 邮件
    if to_alert:
        log.info("触发提醒 %d 条（%s 小时内新发布）", len(to_alert), int(alert_h))
        if not args.dry_run and notify.send(to_alert):
            store.mark_notified([j.fingerprint for j in to_alert])
    else:
        log.info("本次无需提醒")

    store.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
