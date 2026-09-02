"""ASGI Request Logging Middleware — structured log with request ID, method, path, status, latency."""

from __future__ import annotations

import logging
import time
import uuid
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("bhoomi.request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every HTTP request with a unique request ID, method, path, status code, and latency."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = str(uuid.uuid4())
        start_time = time.perf_counter()

        # Store request ID on state so route handlers can access it
        request.state.request_id = request_id

        response: Response = await call_next(request)

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 1)

        logger.info(
            "%s %s %d %.1fms [req=%s]",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
            request_id,
        )

        # Inject X-Request-ID header into every response
        response.headers["X-Request-ID"] = request_id
        return response
