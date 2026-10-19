"""SQLite persistence with numbered SQL migrations.

Every call opens its own short-lived connection, so the dashboard, the
scheduler and a CLI run can share one database file safely (WAL mode plus a
busy timeout). `transaction()` uses BEGIN IMMEDIATE, which takes the write
lock up front; the publishing claim depends on that.

PostgreSQL path: keep the SQL, swap `connect()` for psycopg, translate `?`
placeholders to `%s`, and apply the type changes noted in the migrations.
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from .timeutil import iso

MIGRATIONS = Path(__file__).resolve().parent.parent / "migrations"


class Database:
    def __init__(self, path: Path | str):
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 30000")
        conn.execute("PRAGMA journal_mode = WAL")
        return conn

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            yield conn
            conn.execute("COMMIT")
        except BaseException:
            conn.execute("ROLLBACK")
            raise
        finally:
            conn.close()

    def execute(self, sql: str, params: tuple | list = ()) -> int:
        """Run one write statement in its own transaction; returns lastrowid or rowcount."""
        with self.transaction() as conn:
            cur = conn.execute(sql, params)
            return cur.lastrowid if sql.lstrip().upper().startswith("INSERT") else cur.rowcount

    def query(self, sql: str, params: tuple | list = ()) -> list[dict[str, Any]]:
        conn = self._connect()
        try:
            return [dict(r) for r in conn.execute(sql, params).fetchall()]
        finally:
            conn.close()

    def query_one(self, sql: str, params: tuple | list = ()) -> dict[str, Any] | None:
        rows = self.query(sql, params)
        return rows[0] if rows else None

    def scalar(self, sql: str, params: tuple | list = ()) -> Any:
        row = self.query_one(sql, params)
        return next(iter(row.values())) if row else None

    def migrate(self) -> list[str]:
        applied: list[str] = []
        conn = self._connect()
        try:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)"
            )
            done = {r["version"] for r in conn.execute("SELECT version FROM schema_migrations")}
            for f in sorted(MIGRATIONS.glob("*.sql")):
                version = f.stem
                if version in done:
                    continue
                conn.execute("BEGIN IMMEDIATE")
                try:
                    for statement in _split_sql(f.read_text()):
                        conn.execute(statement)
                    conn.execute("INSERT INTO schema_migrations VALUES (?, ?)", (version, iso()))
                    conn.execute("COMMIT")
                except BaseException:
                    conn.execute("ROLLBACK")
                    raise
                applied.append(version)
        finally:
            conn.close()
        return applied

    # Small helpers used across services -------------------------------------------------

    def audit(self, actor: str, action: str, entity: str, entity_id: Any = None, **detail: Any) -> None:
        self.execute(
            "INSERT INTO audit_log (ts, actor, action, entity, entity_id, detail_json) VALUES (?, ?, ?, ?, ?, ?)",
            (iso(), actor, action, entity, None if entity_id is None else str(entity_id), dumps(detail)),
        )

    def log_error(self, component: str, message: str, detail: str = "", run_id: int | None = None) -> None:
        self.execute(
            "INSERT INTO error_log (ts, run_id, component, message, detail) VALUES (?, ?, ?, ?, ?)",
            (iso(), run_id, component, message[:2000], detail[:8000]),
        )


def _split_sql(text: str) -> list[str]:
    lines = [ln for ln in text.splitlines() if not ln.strip().startswith("--")]
    return [s.strip() for s in "\n".join(lines).split(";") if s.strip()]


def dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def loads(value: str | None, default: Any = None) -> Any:
    if value in (None, ""):
        return default
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default
