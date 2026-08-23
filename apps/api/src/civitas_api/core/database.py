"""Database connection + RowExecutor for the Civitas backend.

Implements the `RowExecutor` protocol expected by the geospatial package:
    def execute(self, sql: str, params: dict | None) -> list[dict]

Connection lifecycle uses a per-request psycopg connection, opened lazily via
a context manager for clean transaction and connection lifecycle management.

For local testing, a `sqlite:///path` URL is transparently swapped to a sqlite3
connection so the api can run without a real Postgres instance.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Any, Self

from civitas_api.core.config import get_settings


def _connect_sqlite(path: str) -> sqlite3.Connection:
    """Connect to a sqlite3 file, with dict-row factory."""
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


class _SQLiteCursor:
    def __init__(self, cur: sqlite3.Cursor) -> None:
        self._cur = cur
        self._description = None

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            self._cur.close()
        except Exception:  # noqa: S110, BLE001
            pass

    def execute(self, sql: str, params: dict | None = None) -> None:
        # Translate psycopg-style %(name)s placeholders to sqlite ? so the
        # same SQL works on both engines. Also strip ::type casts (PostGIS
        # uses these; SQLite does not parse them). When params is a dict
        # we extract values in placeholder order so positional binding works.
        import datetime as _dt
        import re

        def _coerce(v: Any) -> Any:
            if isinstance(v, (_dt.datetime, _dt.date)):
                return v.isoformat()
            return v

        if params is not None and isinstance(params, dict):
            names = re.findall(r"%\(([a-zA-Z_][a-zA-Z0-9_]*)\)s", sql)
            ordered = [_coerce(params[n]) for n in names]
            sql = re.sub(r"%\(([a-zA-Z_][a-zA-Z0-9_]*)\)s", r"?", sql)
            sql = re.sub(r"::\w+", "", sql)
            self._cur.execute(sql, ordered)
            return
        sql = re.sub(r"%\(([a-zA-Z_][a-zA-Z0-9_]*)\)s", r"?", sql)
        sql = re.sub(r"::\w+", "", sql)
        if params is None:
            self._cur.execute(sql)
        else:
            self._cur.execute(sql, params)

    def fetchone(self) -> dict[str, Any] | None:
        row = self._cur.fetchone()
        return dict(row) if row else None

    def fetchall(self) -> list[dict[str, Any]]:
        return [dict(r) for r in self._cur.fetchall()]

    @property
    def description(self):
        return self._description


class _SQLiteConnection:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self._conn.close()

    def cursor(self) -> _SQLiteCursor:
        return _SQLiteCursor(self._conn.cursor())

    def commit(self) -> None:
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()


class _SQLiteExecutor:
    """SQLite-backed executor that returns list[dict] (matches RowExecutor)."""

    def execute(self, sql: str, params: dict[str, object] | None = None) -> list[dict[str, Any]]:
        settings = get_settings()
        path = settings.database_url.replace("sqlite:///", "", 1)
        conn = _connect_sqlite(path)
        try:
            cur = conn.cursor()
            cur.execute(sql, params or {})
            if cur.description is None:
                return []
            return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

    def execute_returning_id(self, sql: str, params: dict[str, object] | None = None) -> str:
        # SQLite variant: caller passes a SELECT … RETURNING-like query.
        rows = self.execute(sql, params)
        if not rows or "incident_id" not in rows[0]:
            raise RuntimeError("INSERT did not return incident_id")
        return str(rows[0]["incident_id"])


@contextmanager
def get_connection():
    """Yield a connection.  Routes to psycopg for postgres URLs, sqlite otherwise."""
    settings = get_settings()
    url = settings.database_url
    if url.startswith("sqlite:///"):
        path = url.replace("sqlite:///", "", 1)
        conn = _connect_sqlite(path)
        try:
            yield _SQLiteConnection(conn)
        finally:
            conn.close()
        return
    if url.startswith(("postgresql://", "postgres://")):
        import psycopg
        from psycopg.rows import dict_row

        conn = psycopg.connect(url, row_factory=dict_row)
        try:
            yield conn
        finally:
            conn.close()
        return
    raise ValueError(f"unsupported DATABASE_URL scheme: {url!r}")


class PostgresExecutor:
    """Adapter that lets the `RowExecutor` protocol hit PostgreSQL/PostGIS.

    `geospatial.queries` returns `(sql, params)` tuples; psycopg binds them
    directly.  For SQLite URLs we fall back to the SQLite executor so the
    backend can be exercised without a live database.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._sqlite_executor = _SQLiteExecutor() if settings.database_url.startswith("sqlite:///") else None

    def execute(self, sql: str, params: dict[str, object] | None = None) -> list[dict[str, Any]]:
        if self._sqlite_executor is not None:
            return self._sqlite_executor.execute(sql, params)
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(sql, params or {})
            if cur.description is None:
                return []
            return list(cur.fetchall())

    def execute_returning_id(self, sql: str, params: dict[str, object] | None = None) -> str:
        if self._sqlite_executor is not None:
            return self._sqlite_executor.execute_returning_id(sql, params)
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(sql, params or {})
            row = cur.fetchone()
            conn.commit()
            if row is None or "incident_id" not in row:
                raise RuntimeError("INSERT did not return incident_id")
            return str(row["incident_id"])