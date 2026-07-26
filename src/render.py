"""生成看板网页 docs/index.html（数据内嵌，GitHub Pages 直接托管）。"""
from __future__ import annotations

import json
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

TEMPLATE = """<!doctype html>
<html lang="zh"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Job Radar</title>
<style>
:root{--bg:#0e1116;--card:#171b22;--line:#262c36;--fg:#e6edf3;--dim:#8b949e;
      --hot:#f85149;--new:#3fb950;--acc:#58a6ff}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
     font:15px/1.55 -apple-system,"PingFang SC","Microsoft YaHei",Segoe UI,sans-serif}
.wrap{max-width:1080px;margin:0 auto;padding:24px 16px 64px}
h1{font-size:22px;margin:0 0 4px}
.sub{color:var(--dim);font-size:13px;margin-bottom:18px}
.stats{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:18px}
.stat{background:var(--card);border:1px solid var(--line);border-radius:10px;
      padding:10px 14px;min-width:96px}
.stat b{display:block;font-size:20px}.stat span{color:var(--dim);font-size:12px}
.bar{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px}
input,select{background:var(--card);border:1px solid var(--line);color:var(--fg);
             border-radius:8px;padding:8px 10px;font-size:14px}
input[type=search]{flex:1;min-width:200px}
.plat{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:20px}
.plat a{background:var(--card);border:1px solid var(--line);color:var(--acc);
        text-decoration:none;font-size:13px;padding:6px 11px;border-radius:999px}
.plat a:hover{border-color:var(--acc)}
.job{background:var(--card);border:1px solid var(--line);border-radius:12px;
     padding:14px 16px;margin-bottom:10px}
.job.isnew{border-color:#2ea04366;box-shadow:inset 3px 0 0 var(--new)}
.jt{font-size:16px;font-weight:600;margin:0 0 4px}
.jt a{color:var(--fg);text-decoration:none}.jt a:hover{color:var(--acc)}
.meta{color:var(--dim);font-size:13px;display:flex;gap:10px;flex-wrap:wrap}
.tags{margin-top:8px;display:flex;gap:6px;flex-wrap:wrap}
.tag{font-size:11px;border:1px solid var(--line);border-radius:999px;
     padding:2px 8px;color:var(--dim)}
.badge{font-size:11px;border-radius:999px;padding:2px 8px;font-weight:600}
.b-new{background:#2ea04326;color:var(--new)}
.b-hot{background:#f8514926;color:var(--hot)}
.b-score{background:#58a6ff22;color:var(--acc)}
.apply{float:right;background:var(--acc);color:#04121f;text-decoration:none;
       font-size:13px;font-weight:600;padding:6px 14px;border-radius:8px}
.empty{color:var(--dim);text-align:center;padding:48px 0}
</style></head><body><div class="wrap">
<h1>Job Radar</h1>
<div class="sub">最近更新：__UPDATED__ · 每小时自动抓取 · 数据源：公司官网 ATS + 免费公开岗位 API</div>
<div class="stats">
  <div class="stat"><b id="s-total">0</b><span>符合条件</span></div>
  <div class="stat"><b id="s-24h" style="color:var(--hot)">0</b><span>24 小时内</span></div>
  <div class="stat"><b id="s-new" style="color:var(--new)">0</b><span>本次新增</span></div>
  <div class="stat"><b id="s-src">0</b><span>数据源</span></div>
</div>
<div class="plat">__PLATFORM_LINKS__</div>
<div class="bar">
  <input type="search" id="q" placeholder="搜索职位 / 公司 / 地点…">
  <select id="fresh">
    <option value="9999">全部时间</option>
    <option value="24">24 小时内</option>
    <option value="72">3 天内</option>
    <option value="168" selected>7 天内</option>
  </select>
  <select id="src"><option value="">全部来源</option></select>
  <select id="sort">
    <option value="score">按匹配度排序</option>
    <option value="date">按发布时间排序</option>
  </select>
</div>
<div id="list"></div>
</div>
<script>
const JOBS = __DATA__;
const $ = s => document.querySelector(s);
const esc = s => (s||"").replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const ago = h => h>=9999 ? "时间未知" : h<1 ? "刚刚" : h<24 ? Math.round(h)+" 小时前"
                 : Math.round(h/24)+" 天前";

const srcs = [...new Set(JOBS.map(j=>j.source))].sort();
srcs.forEach(s => $("#src").insertAdjacentHTML("beforeend", `<option value="${s}">${s}</option>`));
$("#s-src").textContent = srcs.length;
$("#s-24h").textContent = JOBS.filter(j=>j.age_hours<=24).length;
$("#s-new").textContent = JOBS.filter(j=>j.is_new).length;

function render(){
  const q = $("#q").value.toLowerCase().trim();
  const maxAge = +$("#fresh").value, src = $("#src").value, sort = $("#sort").value;
  let rows = JOBS.filter(j =>
    j.age_hours <= maxAge &&
    (!src || j.source === src) &&
    (!q || (j.title+" "+j.company+" "+j.location).toLowerCase().includes(q)));
  rows.sort((a,b) => sort==="score" ? b.score-a.score || a.age_hours-b.age_hours
                                    : a.age_hours-b.age_hours || b.score-a.score);
  $("#s-total").textContent = rows.length;
  $("#list").innerHTML = rows.length ? rows.map(card).join("")
    : '<div class="empty">没有符合条件的岗位。放宽筛选，或在 config.yaml 里调整关键词。</div>';
}
function card(j){
  return `<div class="job ${j.is_new?'isnew':''}">
    <a class="apply" href="${esc(j.url)}" target="_blank" rel="noopener">去投递 →</a>
    <div class="jt"><a href="${esc(j.url)}" target="_blank" rel="noopener">${esc(j.title)}</a></div>
    <div class="meta">
      <span>🏢 ${esc(j.company)}</span><span>📍 ${esc(j.location||"—")}</span>
      <span>🕒 ${ago(j.age_hours)}</span><span>🔗 ${esc(j.source)}</span>
    </div>
    <div class="tags">
      ${j.is_new?'<span class="badge b-new">新发现</span>':''}
      ${j.age_hours<=24?'<span class="badge b-hot">24h 内</span>':''}
      <span class="badge b-score">匹配 ${j.score}</span>
      ${(j.reasons||[]).slice(0,5).map(r=>`<span class="tag">${esc(r)}</span>`).join("")}
    </div></div>`;
}
["q","fresh","src","sort"].forEach(id => {
  $("#"+id).addEventListener(id==="q"?"input":"change", render);
});
render();
</script></body></html>
"""


def _platform_links(cfg: dict) -> str:
    pc = cfg.get("platform_links") or {}
    if not pc.get("enabled"):
        return ""
    loc = pc.get("location", "Germany")
    out = []
    for q in pc.get("queries") or []:
        qe = urllib.parse.quote(q)
        le = urllib.parse.quote(loc)
        links = [
            (f"LinkedIn · {q}",
             f"https://www.linkedin.com/jobs/search/?keywords={qe}&location={le}"
             f"&f_TPR=r86400&sortBy=DD"),
            (f"StepStone · {q}",
             f"https://www.stepstone.de/jobs/{urllib.parse.quote(q.replace(' ', '-'))}"
             f"?sort=2&ag=age_1"),
            (f"Indeed · {q}",
             f"https://de.indeed.com/jobs?q={qe}&l={le}&fromage=1&sort=date"),
            (f"Xing · {q}",
             f"https://www.xing.com/jobs/search?keywords={qe}&sort=date"),
        ]
        out += [f'<a href="{u}" target="_blank" rel="noopener">{t} · 24h</a>'
                for t, u in links]
    return "".join(out)


def render_html(jobs: list, cfg: dict, out_path: str | Path) -> Path:
    data = []
    for j in jobs:
        d = j.to_dict()
        d.pop("description", None)      # 正文不进看板，避免页面体积暴涨
        data.append(d)
    # "</script>" 出现在数据里会截断 <script> 标签，必须转义
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    html = (TEMPLATE
            .replace("__DATA__", payload)
            .replace("__UPDATED__", datetime.now(timezone.utc)
                     .strftime("%Y-%m-%d %H:%M UTC"))
            .replace("__PLATFORM_LINKS__", _platform_links(cfg)))
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(html, encoding="utf-8")
    return p
