"""ASGI middleware enforcing request body size limit (1MB max for JSON requests)."""

from __future__ import annotations

import logging
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger("bhoomi.request_size")

# 1 Megabyte in bytes
MAX_JSON_BODY_BYTES = 1024 * 1024  # 1 MB

# Paths exempt from 1MB limit (e.g. document uploads have their own 20MB validation)
EXEMPT_PREFIXES = (
    "/api/v1/documents/upload",
    "/documents/upload",
)


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Enforces a strict 1MB size limit on request bodies to prevent memory exhaustion / DoS."""

    def __init__(self, app, max_bytes: int = MAX_JSON_BODY_BYTES):
        super().__init__(app)
        self.max_bytes = max_bytes

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path
        if any(path.startswith(prefix) for prefix in EXEMPT_PREFIXES):
            return await call_next(request)

        # 1. Check Content-Length header if present
        content_length_header = request.headers.get("content-length")
        if content_length_header:
            try:
                content_length = int(content_length_header)
                if content_length > self.max_bytes:
                    logger.warning(
                        "Rejected oversized request [%s %s]: %d bytes exceeds %d bytes limit.",
                        request.method,
                        path,
                        content_length,
                        self.max_bytes,
                    )
                    return JSONResponse(
                        status_code=413,
                        content={
                            "detail": (
                                f"Request payload ({content_length:,} bytes) exceeds maximum "
                                f"allowable limit of {self.max_bytes:,} bytes (1MB)."
                            )
                        },
                    )
            except ValueError:
                pass

        # 2. For POST, PUT, PATCH without content-length header or chunked, check body stream
        if request.method in ("POST", "PUT", "PATCH"):
            # Check content length if body was read
            body = await request.body()
            if len(body) > self.max_bytes:
                logger.warning(
                    "Rejected oversized body [%s %s]: %d bytes exceeds %d bytes limit.",
                    request.method,
                    path,
                    len(body),
                    self.max_bytes,
                )
                return JSONResponse(
                    status_code=413,
                    content={
                        "detail": (
                            f"Request payload ({len(body):,} bytes) exceeds maximum "
                            f"allowable limit of {self.max_bytes:,} bytes (1MB)."
                        )
                    },
                )

        return await call_next(request)
