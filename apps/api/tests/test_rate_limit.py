"""Tests for RateLimiter and RateLimitMiddleware."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from civitas_api.core.rate_limit import RateLimiter, RateLimitMiddleware


def test_rate_limiter_allows_and_throttles(monkeypatch) -> None:
    monkeypatch.setenv("CIVITAS_DISABLE_RATE_LIMITING", "0")
    test_app = FastAPI()
    limiter = RateLimiter(default_limit=3, default_window_seconds=10, sensitive_limit=2, sensitive_window_seconds=10)
    test_app.add_middleware(RateLimitMiddleware, limiter=limiter)

    @test_app.get("/test-endpoint")
    def sample_endpoint():
        return {"status": "ok"}

    client = TestClient(test_app)

    # 3 allowed requests
    for i in range(3):
        res = client.get("/test-endpoint")
        assert res.status_code == 200, f"Request {i+1} failed"
        assert "X-RateLimit-Remaining" in res.headers

    # 4th request must be throttled
    res = client.get("/test-endpoint")
    assert res.status_code == 429
    assert res.headers.get("Retry-After") is not None
    body = res.json()
    assert body["success"] is False
    assert body["error"]["code"] == "RATE_LIMIT_EXCEEDED"


def test_health_routes_bypass_rate_limiting(monkeypatch) -> None:
    monkeypatch.setenv("CIVITAS_DISABLE_RATE_LIMITING", "0")
    test_app = FastAPI()
    limiter = RateLimiter(default_limit=1, default_window_seconds=10)
    test_app.add_middleware(RateLimitMiddleware, limiter=limiter)

    @test_app.get("/health")
    def health_endpoint():
        return {"status": "healthy"}

    client = TestClient(test_app)

    for _ in range(5):
        res = client.get("/health")
        assert res.status_code == 200
