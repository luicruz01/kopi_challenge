"""Observability setup: logging and optional metrics."""
import json
import logging
import os
import sys
import time

# Optional prometheus imports - only used if ENABLE_METRICS=1
try:
    from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    Counter = Histogram = generate_latest = CONTENT_TYPE_LATEST = None


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        # Check if message is already JSON
        try:
            # If message is already a JSON string, parse and return it
            if isinstance(record.msg, str) and record.msg.strip().startswith("{"):
                return record.msg
        except (json.JSONDecodeError, AttributeError):
            pass

        # Create structured log entry
        log_data = {
            "timestamp": time.time(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def setup_logging(log_level: str = "INFO") -> None:
    """Setup structured JSON logging."""
    # Configure root logger with JSON formatter
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        handlers=[handler],
        format="%(message)s",  # Format is handled by JSONFormatter
    )

    # Silence some noisy loggers
    logging.getLogger("uvicorn.access").disabled = True


class Metrics:
    """Prometheus metrics collector (optional)."""

    def __init__(self):
        self.enabled = os.getenv("ENABLE_METRICS", "0") == "1"

        if self.enabled and PROMETHEUS_AVAILABLE:
            # HTTP request counter
            self.http_requests_total = Counter(
                "http_requests_total", "Total HTTP requests", ["method", "path", "status"]
            )

            # HTTP request latency histogram
            self.http_request_duration_seconds = Histogram(
                "http_request_duration_seconds", "HTTP request latency", ["method", "path"]
            )
        else:
            self.http_requests_total = None
            self.http_request_duration_seconds = None

    def record_request(self, method: str, path: str, status: int, duration: float) -> None:
        """Record HTTP request metrics."""
        if not self.enabled or not PROMETHEUS_AVAILABLE:
            return

        if self.http_requests_total:
            self.http_requests_total.labels(method=method, path=path, status=str(status)).inc()

        if self.http_request_duration_seconds:
            self.http_request_duration_seconds.labels(method=method, path=path).observe(duration)

    def get_metrics(self) -> str | None:
        """Get Prometheus metrics in text format."""
        if not self.enabled or not PROMETHEUS_AVAILABLE:
            return None

        return generate_latest().decode("utf-8")

    def get_content_type(self) -> str | None:
        """Get Prometheus content type."""
        if not self.enabled or not PROMETHEUS_AVAILABLE:
            return None

        return CONTENT_TYPE_LATEST


# Global metrics instance
metrics = Metrics()
