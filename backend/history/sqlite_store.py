"""Durable SQLite-backed history store for Veritas synthesis results.

Replaces the per-machine ephemeral JSON file. Backs onto a Fly volume
mount (/data by default) so results survive process restarts, machine
replacement, and redeploys.

Contract:
- Exact-ID access only; foreign/unknown ids return None indistinguishably.
- Atomic commits (WAL journal); a storage outage raises HistoryStoreError,
  which the app edge sanitizes — no partial writes, no silent fallback.
- Optional retention: VERITAS_HISTORY_RETENTION_DAYS > 0 lazily expires
  entries older than the window (delete still always works).
- Migration: import legacy synthesis_history.json once into an empty DB.
"""

import json
import os
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional


class HistoryStoreError(Exception):
    """Storage-layer failure; callers must sanitize before the edge."""


_SCHEMA = """
CREATE TABLE IF NOT EXISTS history (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    question TEXT NOT NULL,
    answer_json TEXT NOT NULL,
    trace_json TEXT,
    owner_subject TEXT,
    receipt_ref TEXT,
    retention_state TEXT NOT NULL DEFAULT 'retained'
);
"""


class SqliteHistoryStore:
    """Durable history store; drop-in replacement for HistoryStore."""

    def __init__(self, db_path: Path = None,
                 retention_days: int = 0,
                 legacy_json: Path = None):
        if db_path is None:
            db_path = Path(
                os.getenv("VERITAS_HISTORY_DB", "/data/history.db"))
        self.db_path = Path(db_path)
        self.retention_days = retention_days
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(
                str(self.db_path), check_same_thread=False)
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA busy_timeout=5000")
            self._conn.executescript(_SCHEMA)
            self._conn.commit()
        except (OSError, sqlite3.Error) as e:
            raise HistoryStoreError(f"history store init failed: {e}")
        if legacy_json:
            self._migrate_legacy(Path(legacy_json))

    def _migrate_legacy(self, legacy_json: Path) -> int:
        """One-time import of the legacy JSON history into an empty DB."""
        if not legacy_json.exists():
            return 0
        try:
            rows = json.loads(legacy_json.read_text(encoding="utf-8"))
            if not isinstance(rows, list):
                return 0
            empty = self._conn.execute(
                "SELECT COUNT(*) FROM history").fetchone()[0] == 0
            if not empty:
                return 0
            with self._conn:
                for e in rows:
                    self._conn.execute(
                        "INSERT OR IGNORE INTO history"
                        " (id, created_at, question, answer_json, trace_json)"
                        " VALUES (?,?,?,?,?)",
                        (e["id"], e.get("timestamp") or e.get("created_at"),
                         e["question"], json.dumps(e.get("answer") or {}),
                         json.dumps(e.get("trace") or {})))
            return len(rows)
        except (OSError, ValueError, sqlite3.Error, KeyError):
            return 0

    def _expired(self, created_at: str) -> bool:
        if self.retention_days <= 0:
            return False
        try:
            ts = datetime.fromisoformat(created_at)
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            return datetime.now(timezone.utc) - ts > timedelta(
                days=self.retention_days)
        except (ValueError, TypeError):
            return False

    def _row_to_entry(self, row) -> Optional[Dict]:
        if row is None:
            return None
        created = row[1]
        if self._expired(created):
            return None
        return {
            "id": row[0],
            "timestamp": created,
            "question": row[2],
            "answer": json.loads(row[3] or "{}"),
            "trace": json.loads(row[4] or "{}"),
        }

    def save_synthesis(self, question: str, answer: Dict,
                       trace: Dict, owner_subject: str = None,
                       receipt_ref: str = None) -> str:
        session_id = str(uuid.uuid4())
        try:
            with self._conn:
                self._conn.execute(
                    "INSERT INTO history (id, created_at, question,"
                    " answer_json, trace_json, owner_subject, receipt_ref)"
                    " VALUES (?,?,?,?,?,?,?)",
                    (session_id, datetime.now(timezone.utc).isoformat(),
                     question, json.dumps(answer or {}),
                     json.dumps(trace or {}), owner_subject, receipt_ref))
        except sqlite3.Error as e:
            raise HistoryStoreError(f"history write failed: {e}")
        return session_id

    def get_all_history(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        try:
            rows = self._conn.execute(
                "SELECT id, created_at, question, answer_json FROM history"
                " ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset)).fetchall()
        except sqlite3.Error as e:
            raise HistoryStoreError(f"history read failed: {e}")
        out = []
        for r in rows:
            if self._expired(r[1]):
                continue
            answer = json.loads(r[3] or "{}")
            out.append({
                "id": r[0],
                "timestamp": r[1],
                "question": r[2],
                "preview": answer.get("ideas", [{}])[0].get("title", "")
                           if answer.get("ideas") else "",
                "idea_count": len(answer.get("ideas", [])),
                "source_count": len(answer.get("sources", {})),
            })
        return out

    def get_history_by_id(self, session_id: str) -> Optional[Dict]:
        if not isinstance(session_id, str) or not session_id:
            return None
        try:
            row = self._conn.execute(
                "SELECT id, created_at, question, answer_json, trace_json"
                " FROM history WHERE id=?",
                (session_id,)).fetchone()
        except sqlite3.Error as e:
            raise HistoryStoreError(f"history read failed: {e}")
        return self._row_to_entry(row)

    def delete_history(self, session_id: str) -> bool:
        try:
            cur = self._conn.execute(
                "DELETE FROM history WHERE id=?", (session_id,))
            self._conn.commit()
            return cur.rowcount > 0
        except sqlite3.Error as e:
            raise HistoryStoreError(f"history delete failed: {e}")

    def close(self):
        try:
            self._conn.close()
        except Exception:
            pass
