"""邮件提醒。凭据全部走环境变量 / GitHub Secrets，不写进仓库。"""
from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from email.utils import formataddr

ROW = """
<tr><td style="padding:12px 0;border-bottom:1px solid #e5e7eb">
  <div style="font-size:16px;font-weight:600">
    <a href="{url}" style="color:#111827;text-decoration:none">{title}</a></div>
  <div style="color:#6b7280;font-size:13px;margin:4px 0">
    {company} · {location} · {ago} · {source} · 匹配度 {score}</div>
  <a href="{url}" style="display:inline-block;background:#2563eb;color:#fff;
     font-size:13px;font-weight:600;padding:7px 14px;border-radius:6px;
     text-decoration:none;margin-top:4px">立即投递 →</a>
</td></tr>"""


def _ago(h: float) -> str:
    if h >= 9999:
        return "时间未知"
    if h < 1:
        return "刚刚发布"
    if h < 24:
        return f"{round(h)} 小时前"
    return f"{round(h / 24)} 天前"


def build_html(jobs: list) -> str:
    rows = "".join(
        ROW.format(url=j.url, title=j.title, company=j.company,
                   location=j.location or "—", ago=_ago(j.age_hours),
                   source=j.source, score=j.score)
        for j in jobs)
    return f"""<html><body style="font-family:-apple-system,Segoe UI,sans-serif;
      background:#f9fafb;padding:24px">
      <div style="max-width:640px;margin:0 auto;background:#fff;border-radius:12px;padding:24px">
      <h2 style="margin:0 0 4px">发现 {len(jobs)} 个新岗位</h2>
      <p style="color:#6b7280;font-size:13px;margin:0 0 12px">
        来自公司官网招聘系统与公开岗位 API，均为近期发布。</p>
      <table style="width:100%;border-collapse:collapse">{rows}</table>
      </div></body></html>"""


def send(jobs: list) -> bool:
    """需要环境变量：SMTP_HOST SMTP_PORT SMTP_USER SMTP_PASS MAIL_TO"""
    if not jobs:
        return False
    host = os.getenv("SMTP_HOST")
    user = os.getenv("SMTP_USER")
    pwd = os.getenv("SMTP_PASS")
    to = os.getenv("MAIL_TO") or user
    if not (host and user and pwd and to):
        print("[notify] 未配置 SMTP 环境变量，跳过邮件推送")
        return False

    msg = EmailMessage()
    msg["Subject"] = f"[Job Radar] {len(jobs)} 个新岗位 · 最高匹配 {max(j.score for j in jobs)}"
    msg["From"] = formataddr(("Job Radar", user))
    msg["To"] = to
    msg.set_content("\n\n".join(f"{j.title} @ {j.company} ({j.location})\n{j.url}"
                                for j in jobs))
    msg.add_alternative(build_html(jobs), subtype="html")

    port = int(os.getenv("SMTP_PORT", "587"))
    try:
        if port == 465:
            with smtplib.SMTP_SSL(host, port, timeout=30) as s:
                s.login(user, pwd)
                s.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=30) as s:
                s.starttls()
                s.login(user, pwd)
                s.send_message(msg)
        print(f"[notify] 已发送邮件，{len(jobs)} 个岗位 -> {to}")
        return True
    except Exception as e:  # noqa: BLE001
        print(f"[notify] 邮件发送失败: {e}")
        return False
