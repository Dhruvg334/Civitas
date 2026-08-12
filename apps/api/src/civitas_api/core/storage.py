"""Object storage adapter.

Two interchangeable backends:

- `SupabaseStorageAdapter` — uploads to a Supabase Storage bucket using
  the service-role key. Used in production.
- `LocalDiskStorageAdapter` — writes to a directory on disk. Used in
  tests and when no Supabase creds are set.

The backend is selected at startup based on settings:

    if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY and STORAGE_BUCKET:
        -> SupabaseStorageAdapter
    else:
        -> LocalDiskStorageAdapter (./storage/<bucket>/)

The adapter exposes three methods:
    put(object_path, bytes, content_type) -> storage_path
    signed_url(object_path, ttl_seconds)  -> str
    head(object_path)                     -> dict | None
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


class StorageAdapter(ABC):
    bucket: str

    @abstractmethod
    def put(self, object_path: str, data: bytes, content_type: str) -> str: ...

    @abstractmethod
    def signed_url(self, object_path: str, ttl_seconds: int = 3600) -> str: ...

    @abstractmethod
    def head(self, object_path: str) -> dict[str, Any] | None: ...

    @abstractmethod
    def get(self, object_path: str) -> bytes: ...


class LocalDiskStorageAdapter(StorageAdapter):
    def __init__(self, bucket: str, root: Path) -> None:
        self.bucket = bucket
        self._root = root / bucket
        self._root.mkdir(parents=True, exist_ok=True)

    def _resolve(self, object_path: str) -> Path:
        # Reject path traversal — object_path is constructed by us, but be safe.
        if ".." in object_path.split("/"):
            raise ValueError(f"invalid object_path: {object_path!r}")
        return self._root / object_path

    def put(self, object_path: str, data: bytes, content_type: str) -> str:
        target = self._resolve(object_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        return f"local://{self.bucket}/{object_path}"

    def signed_url(self, object_path: str, ttl_seconds: int = 3600) -> str:
        # Local mode has no real signing; return a deterministic dev URL.
        return f"local://{self.bucket}/{object_path}?ttl={ttl_seconds}"

    def head(self, object_path: str) -> dict[str, Any] | None:
        target = self._resolve(object_path)
        if not target.exists():
            return None
        st = target.stat()
        return {"size": st.st_size, "modified": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat()}

    def get(self, object_path: str) -> bytes:
        target = self._resolve(object_path)
        if not target.exists():
            raise FileNotFoundError(object_path)
        return target.read_bytes()


class SupabaseStorageAdapter(StorageAdapter):
    """Minimal Supabase Storage client via the REST API.

    Uses the service-role key (server-only). Does NOT depend on
    supabase-py — talks to the Storage HTTP endpoint directly with
    httpx, which is already a FastAPI transitive dep.
    """

    def __init__(self, url: str, key: str, bucket: str) -> None:
        self._base = url.rstrip("/")
        self._key = key
        self.bucket = bucket

    def _auth_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._key}",
            "apikey": self._key,
        }

    def put(self, object_path: str, data: bytes, content_type: str) -> str:
        import httpx

        url = f"{self._base}/storage/v1/object/{self.bucket}/{object_path}"
        headers = self._auth_headers()
        headers["Content-Type"] = content_type
        headers["x-upsert"] = "true"
        resp = httpx.post(url, headers=headers, content=data, timeout=30)
        if resp.status_code not in (200, 201):
            raise RuntimeError(f"storage upload failed: {resp.status_code} {resp.text}")
        return f"supabase://{self.bucket}/{object_path}"

    def signed_url(self, object_path: str, ttl_seconds: int = 3600) -> str:
        import httpx

        url = f"{self._base}/storage/v1/object/sign/{self.bucket}/{object_path}"
        resp = httpx.post(
            url,
            headers={**self._auth_headers(), "Content-Type": "application/json"},
            json={"expiresIn": ttl_seconds},
            timeout=10,
        )
        if resp.status_code != 200:
            raise RuntimeError(f"signed URL failed: {resp.status_code} {resp.text}")
        signed = resp.json().get("signedURL") or resp.json().get("signed_url")
        if not signed:
            raise RuntimeError(f"signed URL missing in response: {resp.text}")
        return f"{self._base}/storage/v1{signed}" if signed.startswith("/") else signed

    def head(self, object_path: str) -> dict[str, Any] | None:
        # Supabase Storage does not expose HEAD; do a signed URL probe instead.
        try:
            self.signed_url(object_path, ttl_seconds=1)
            return {"exists": True}
        except Exception:  # noqa: BLE001
            return None

    def get(self, object_path: str) -> bytes:
        import httpx
        url = f"{self._base}/storage/v1/object/{self.bucket}/{object_path}"
        resp = httpx.get(url, headers=self._auth_headers(), timeout=30)
        if resp.status_code != 200:
            raise FileNotFoundError(f"storage object unavailable: {object_path} ({resp.status_code})")
        return resp.content


_adapter: StorageAdapter | None = None


def get_storage() -> StorageAdapter:
    """Return the singleton storage adapter, selected at first call."""
    global _adapter
    if _adapter is not None:
        return _adapter
    from civitas_api.core.config import get_settings

    s = get_settings()
    bucket = s.storage_bucket or "report-media"
    if s.supabase_url and s.supabase_service_role_key:
        _adapter = SupabaseStorageAdapter(s.supabase_url, s.supabase_service_role_key, bucket)
    else:
        root = Path(os.environ.get("CIVITAS_STORAGE_ROOT", "./storage")).resolve()
        _adapter = LocalDiskStorageAdapter(bucket=bucket, root=root)
    return _adapter


def reset_storage_for_tests() -> None:
    """Clear the singleton so tests can swap backends between runs."""
    global _adapter
    _adapter = None