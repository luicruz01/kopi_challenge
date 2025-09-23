"""Middleware for request handling, timeouts, and logging."""
import asyncio
import json
import logging
import time
from collections.abc import Callable
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from .models import ErrorEnvelope, ErrorInfo

logger = logging.getLogger(__name__)


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Middleware to add request ID to requests and responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get or generate request ID
        request_id = request.headers.get("X-Request-Id", str(uuid4()))

        # Add to request state
        request.state.request_id = request_id

        # Call next middleware/endpoint
        response = await call_next(request)

        # Add to response headers
        response.headers["X-Request-Id"] = request_id

        return response


class TimeoutMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce request timeouts."""

    def __init__(self, app, timeout_seconds: int = 29):
        super().__init__(app)
        self.timeout_seconds = timeout_seconds

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            # Wrap the call with a timeout
            response = await asyncio.wait_for(call_next(request), timeout=self.timeout_seconds)
            return response
        except TimeoutError:
            # Return timeout error
            request_id = getattr(request.state, "request_id", str(uuid4()))

            error_response = ErrorEnvelope(
                error=ErrorInfo(
                    code="timeout",
                    message="Request exceeded time limit",
                    details={},
                    trace_id=request_id,
                )
            )

            response = JSONResponse(status_code=504, content=error_response.model_dump())
            response.headers["X-Request-Id"] = request_id
            return response


class AccessLogMiddleware(BaseHTTPMiddleware):
    """Middleware for structured access logging."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        # Get request ID
        request_id = getattr(request.state, "request_id", str(uuid4()))

        response = await call_next(request)

        # Calculate latency
        latency_ms = round((time.time() - start_time) * 1000, 2)

        # Log access in JSON format
        log_data = {
            "timestamp": time.time(),
            "level": "INFO",
            "logger": "access",
            "msg": "Request processed",
            "path": str(request.url.path),
            "method": request.method,
            "status": response.status_code,
            "latency_ms": latency_ms,
            "trace_id": request_id,
        }

        # Log as JSON
        logger.info(json.dumps(log_data))

        return response
