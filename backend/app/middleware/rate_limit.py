"""IP-based sliding window rate limiter middleware for BhoomiSetu API."""

from __future__ import annotations

import logging
import threading
import time
from collections import deque
from typing import Callable, Deque, Dict, Tuple

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger("bhoomi.ratelimit")

# Specific limits per route prefix: (prefix, limit, window_seconds)
ROUTE_LIMITS: list[Tuple[str, int, int]] = [
    # Auth login: 10 attempts per minute to prevent brute force
    ("/api/v1/auth/login", 10, 60),
    ("/auth/login", 10, 60),
    # Analytics and Dashboard
    ("/api/v1/analytics", 100, 60),
    ("/api/v1/dashboard", 100, 60),
    ("/analytics", 100, 60),
]


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Per-IP sliding window rate limiter.

    Applies calibrated limits:
    - Auth login: 10 requests / 60 seconds
    - Analytics / Dashboard: 100 requests / 60 seconds
    """

    def __init__(self, app):
        super().__init__(app)
        # Key: (ip, route_prefix) -> deque of timestamps
        self._windows: Dict[Tuple[str, str], Deque[float]] = {}
        self._lock = threading.Lock()

    def _get_client_ip(self, request: Request) -> str:
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _get_matching_rule(self, path: str) -> Tuple[str, int, int] | None:
        for prefix, limit, window in ROUTE_LIMITS:
            if path.startswith(prefix):
                return prefix, limit, window
        return None

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        rule = self._get_matching_rule(request.url.path)
        if not rule:
            return await call_next(request)

        prefix, limit, window_seconds = rule
        ip = self._get_client_ip(request)
        key = (ip, prefix)
        now = time.monotonic()
        window_start = now - window_seconds

        with self._lock:
            if key not in self._windows:
                self._windows[key] = deque()

            dq = self._windows[key]

            # Evict timestamps older than the window
            while dq and dq[0] < window_start:
                dq.popleft()

            if len(dq) >= limit:
                oldest = dq[0]
                retry_after = int(window_seconds - (now - oldest)) + 1
                logger.warning(
                    "Rate limit exceeded for IP=%s on %s (%d requests in %ds)",
                    ip,
                    request.url.path,
                    len(dq),
                    window_seconds,
                )
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": f"Rate limit exceeded on {prefix}. Too many requests.",
                        "retry_after_seconds": retry_after,
                        "limit": limit,
                        "window_seconds": window_seconds,
                    },
                    headers={"Retry-After": str(retry_after)},
                )

            dq.append(now)

        return await call_next(request)
