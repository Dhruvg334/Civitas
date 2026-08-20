"""In-memory sliding-window rate limiting middleware for FastAPI."""

from __future__ import annotations

import os
import time
from collections import defaultdict
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from civitas_api.core.envelope import error_envelope


class RateLimiter:
    """Sliding-window rate limiter tracking requests per client key."""

    def __init__(
        self,
        default_limit: int = 300,
        default_window_seconds: int = 60,
        sensitive_limit: int = 60,
        sensitive_window_seconds: int = 60,
    ) -> None:
        self.default_limit = default_limit
        self.default_window_seconds = default_window_seconds
        self.sensitive_limit = sensitive_limit
        self.sensitive_window_seconds = sensitive_window_seconds
        # key -> list of timestamps
        self._history: dict[str, list[float]] = defaultdict(list)
        self._last_cleanup = time.time()

    def _get_client_key(self, request: Request) -> str:
        # Prefer X-Forwarded-For if behind a reverse proxy (e.g. Render / Cloudflare), fallback to client host
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "127.0.0.1"
        return client_ip

    def _is_sensitive_route(self, request: Request) -> bool:
        path = request.url.path.rstrip("/")
        method = request.method.upper()
        return method == "POST" and (
            path == "/api/v1/reports"
            or path.endswith("/media")
            or path == "/api/v1/map-extract"
            or path == "/api/v1/ml/analyze"
        )

    def _cleanup(self, now: float) -> None:
        if now - self._last_cleanup < 60:
            return
        self._last_cleanup = now
        max_window = max(self.default_window_seconds, self.sensitive_window_seconds)
        threshold = now - max_window
        stale_keys = []
        for key, timestamps in self._history.items():
            self._history[key] = [t for t in timestamps if t > threshold]
            if not self._history[key]:
                stale_keys.append(key)
        for key in stale_keys:
            self._history.pop(key, None)

    def is_allowed(self, request: Request) -> tuple[bool, int, int]:
        """Check if request is allowed. Returns (allowed, retry_after_seconds, remaining_requests)."""
        now = time.time()
        self._cleanup(now)

        is_sensitive = self._is_sensitive_route(request)
        limit = self.sensitive_limit if is_sensitive else self.default_limit
        window = self.sensitive_window_seconds if is_sensitive else self.default_window_seconds

        client_key = f"{self._get_client_key(request)}:{'sens' if is_sensitive else 'gen'}"
        threshold = now - window

        # Filter active timestamps in window
        active = [t for t in self._history[client_key] if t > threshold]
        self._history[client_key] = active

        if len(active) >= limit:
            oldest = active[0]
            retry_after = max(1, int(window - (now - oldest)))
            return False, retry_after, 0

        self._history[client_key].append(now)
        remaining = max(0, limit - len(self._history[client_key]))
        return True, 0, remaining


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI/Starlette middleware enforcing rate limits."""

    def __init__(self, app, limiter: RateLimiter | None = None) -> None:
        super().__init__(app)
        self.limiter = limiter or RateLimiter()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check if rate limiting is globally disabled (e.g. during specific tests)
        if os.getenv("CIVITAS_DISABLE_RATE_LIMITING", "").lower() in {"1", "true", "yes"}:
            return await call_next(request)

        # Health / live probes are never rate limited
        if request.url.path in {"/health", "/live", "/api/v1/health"}:
            return await call_next(request)

        allowed, retry_after, remaining = self.limiter.is_allowed(request)
        if not allowed:
            return JSONResponse(
                status_code=429,
                content=error_envelope(
                    code="RATE_LIMIT_EXCEEDED",
                    message="Too many requests. Please slow down and try again later.",
                    retryable=True,
                ),
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Remaining": "0",
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
