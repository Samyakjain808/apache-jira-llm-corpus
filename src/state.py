from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS cursors(
  project TEXT PRIMARY KEY,
  start_at INTEGER NOT NULL DEFAULT 0,
  last_issue_key TEXT,
  watermark_updated TEXT
);
"""

class State:
    def __init__(self, db_path: str):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute(SCHEMA)
        self.conn.commit()

    def get(self, project: str) -> tuple[int, Optional[str], Optional[str]]:
        cur = self.conn.execute(
            "SELECT start_at, last_issue_key, watermark_updated FROM cursors WHERE project=?",
            (project,),
        ).fetchone()
        if not cur:
            return 0, None, None
        return int(cur[0]), cur[1], cur[2]

    def update(self, project: str, start_at: int, last_issue_key: Optional[str], watermark_updated: Optional[str]):
        self.conn.execute(
            "INSERT INTO cursors(project, start_at, last_issue_key, watermark_updated) VALUES(?,?,?,?)\n"
            "ON CONFLICT(project) DO UPDATE SET start_at=excluded.start_at, last_issue_key=excluded.last_issue_key, watermark_updated=excluded.watermark_updated",
            (project, start_at, last_issue_key, watermark_updated),
        )
        self.conn.commit()
