from __future__ import annotations

import logging
import time
from typing import Callable
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("jira_monitor")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Attach request ids and emit structured timing logs."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Response]
    ) -> Response:
        request_id = request.headers.get("x-request-id", str(uuid4()))
        start_time = time.perf_counter()
        request.state.request_id = request_id
        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                "request failed",
                extra={"request_id": request_id, "path": request.url.path},
            )
            raise

        process_time = (time.perf_counter() - start_time) * 1000
        response.headers["x-request-id"] = request_id
        logger.info(
            "request complete",
            extra={
                "request_id": request_id,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(process_time, 2),
            },
        )
        return response
