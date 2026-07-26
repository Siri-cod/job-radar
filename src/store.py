"""SQLite 去重存储：记录每个岗位指纹的首次出现时间，用于判断'是否是新岗位'。"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class Store:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.con = sqlite3.connect(self.path)
        self.con.execute("""
            CREATE TABLE IF NOT EXISTS seen (
                fp         TEXT PRIMARY KEY,
                first_seen TEXT NOT NULL,
                title      TEXT,
                company    TEXT,
                url        TEXT,
                notified   INTEGER DEFAULT 0
            )""")
        self.con.commit()

    def is_new(self, job) -> bool:
        cur = self.con.execute("SELECT first_seen FROM seen WHERE fp=?", (job.fingerprint,))
        row = cur.fetchone()
        if row:
            job.first_seen = row[0]
            return False
        now = datetime.now(timezone.utc).isoformat()
        self.con.execute(
            "INSERT INTO seen (fp, first_seen, title, company, url) VALUES (?,?,?,?,?)",
            (job.fingerprint, now, job.title, job.company, job.url))
        job.first_seen = now
        return True

    def mark_notified(self, fps: list[str]) -> None:
        self.con.executemany("UPDATE seen SET notified=1 WHERE fp=?", [(f,) for f in fps])
        self.con.commit()

    def was_notified(self, fp: str) -> bool:
        cur = self.con.execute("SELECT notified FROM seen WHERE fp=?", (fp,))
        row = cur.fetchone()
        return bool(row and row[0])

    def commit(self) -> None:
        self.con.commit()

    def close(self) -> None:
        self.con.commit()
        self.con.close()
