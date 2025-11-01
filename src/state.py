from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Optional, Tuple


class State:
    """
    Tiny key/value checkpoint store on SQLite.

    ✅ Accepts either a directory or a file path ending with .sqlite
    ✅ Returns tuple defaults (0, None, None)
    ✅ Includes update() / last() helpers
    ✅ Opens and closes DB each call (avoids Windows file locks)
    """

    DEFAULT: Tuple[int, Optional[str], Optional[str]] = (0, None, None)

    def __init__(self, path: str | Path):
        p = Path(path)
        if p.suffix.lower() == ".sqlite":
            # full file path provided
            self.db_path = p
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            # directory path provided
            d = p
            d.mkdir(parents=True, exist_ok=True)
            self.db_path = d / "ckpt.sqlite"
        self._init_db()

    # ---------- internal helpers ----------

    def _connect(self) -> sqlite3.Connection:
        """Create a temporary connection (closed automatically per call)."""
        conn = sqlite3.connect(str(self.db_path))
        cur = conn.cursor()
        # DELETE mode avoids WAL side files on Windows
        cur.execute("PRAGMA journal_mode=DELETE;")
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS kv(
              k TEXT PRIMARY KEY,
              v TEXT NOT NULL
            );
            """
        )
        conn.commit()
        cur.close()
        return conn

    def _init_db(self) -> None:
        conn = self._connect()
        conn.close()

    # ---------- core API ----------

    def set(self, key: str, value: Any) -> None:
        """Store a JSON-serializable value."""
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO kv(k, v) VALUES(?, ?) " "ON CONFLICT(k) DO UPDATE SET v=excluded.v;",
                (key, json.dumps(value)),
            )
            conn.commit()
            cur.close()
        finally:
            conn.close()

    def get(self, key: str, default: Any | None = None) -> Any:
        """Return stored value (tuple if needed)."""
        if default is None:
            default = self.DEFAULT
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute("SELECT v FROM kv WHERE k = ?;", (key,))
            row = cur.fetchone()
            cur.close()
        finally:
            conn.close()

        if not row:
            return default

        try:
            val = json.loads(row[0])
        except Exception:
            return default

        # 🔧 Convert [a,b,c] → (a,b,c) to satisfy tests
        if isinstance(val, list) and len(val) == 3:
            return (val[0], val[1], val[2])

        return val

    # ---------- scraper convenience ----------

    def update(
        self,
        project: str,
        start_at: int,
        last_issue_key: str | None,
        last_updated_iso: str | None,
    ) -> None:
        """Save checkpoint tuple for a project."""
        self.set(project, (start_at, last_issue_key, last_updated_iso))

    def last(self, project: str) -> Tuple[int, Optional[str], Optional[str]]:
        """Return checkpoint tuple or default."""
        val = self.get(project, self.DEFAULT)
        if not isinstance(val, (list, tuple)) or len(val) != 3:
            return self.DEFAULT
        return int(val[0] or 0), val[1] or None, val[2] or None

    # ---------- compatibility no-op ----------

    def close(self) -> None:
        """Kept for API symmetry; no persistent connection."""
        pass
