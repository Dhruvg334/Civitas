"""Optional PostGIS client.

psycopg is an extra dependency (``pip install civitas-geospatial[postgres]``).
The client is created lazily so the rest of the package stays importable in
pure-offline mode. Connection string comes from the CIVITAS_POSTGIS_DSN
environment variable; never from source control.
"""

from __future__ import annotations

import os
from typing import Any


class PostGISClient:
    """Thin psycopg3 wrapper exposing the RowExecutor protocol."""

    def __init__(self, dsn: str | None = None) -> None:
        self.dsn = dsn or os.environ.get("CIVITAS_POSTGIS_DSN")
        if not self.dsn:
            raise ValueError(
                "No CIVITAS_POSTGIS_DSN set; configure the connection string "
                "as an environment variable."
            )
        self._conn: Any = None

    def connect(self) -> Any:
        if self._conn is None:
            try:
                import psycopg  # type: ignore[import-not-found]  # optional extra
            except ImportError as exc:  # pragma: no cover - depends on environment
                raise ImportError(
                    "psycopg is required for PostGIS mode; install "
                    "'civitas-geospatial[postgres]'."
                ) from exc
            self._conn = psycopg.connect(self.dsn)
        return self._conn

    def execute(self, sql: str, params: dict[str, object] | None = None) -> list[dict[str, Any]]:
        conn = self.connect()
        with conn.cursor() as cur:
            cur.execute(sql, params or {})
            cols = [d.name for d in cur.description] if cur.description else []
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None