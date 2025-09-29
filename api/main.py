"""FastAPI application with chat, health, and metrics endpoints."""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import ValidationError

from .handlers import ChatHandler
from .middleware import AccessLogMiddleware, RequestIdMiddleware, TimeoutMiddleware
from .models import ChatRequest, ChatResponse, ErrorEnvelope, ErrorInfo, HealthResponse
from .observability import metrics, setup_logging
from .storage import create_store
from .utils import get_git_hash

# Environment variables
APP_ENV = os.getenv("APP_ENV", "local")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
PORT = int(os.getenv("PORT", "8000"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "29"))
REDIS_URL = os.getenv("REDIS_URL")
ENABLE_METRICS = os.getenv("ENABLE_METRICS", "0") == "1"

# Global variables - these will be set during lifespan startup
store = None
chat_handler = None


def initialize_dependencies():
    """Initialize storage and chat handler."""
    global store, chat_handler

    if store is None or chat_handler is None:
        # Setup logging
        setup_logging(LOG_LEVEL)

        # Initialize storage and handler
        store = create_store(REDIS_URL)
        chat_handler = ChatHandler(store)

    return store, chat_handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager."""
    global store, chat_handler

    # Initialize dependencies
    store, chat_handler = initialize_dependencies()

    # Store them in app state as well for access in endpoints
    app.state.store = store
    app.state.chat_handler = chat_handler

    yield

    # Cleanup (if needed)
    pass


# Create FastAPI app
app = FastAPI(title="Chat API", version="1.0.0", lifespan=lifespan)

# Add CORS middleware (allow all for demo)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(AccessLogMiddleware)
app.add_middleware(TimeoutMiddleware, timeout_seconds=REQUEST_TIMEOUT)
app.add_middleware(RequestIdMiddleware)


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle Pydantic validation errors."""
    request_id = getattr(request.state, "request_id", "unknown")

    error_response = ErrorEnvelope(
        error=ErrorInfo(
            code="validation_error",
            message="Invalid request data",
            details={"validation_errors": exc.errors()},
            trace_id=request_id,
        )
    )

    return JSONResponse(status_code=400, content=error_response.model_dump())


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    request_id = getattr(request.state, "request_id", "unknown")

    # If detail is already in error format, return as-is
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)

    # Map status codes to error codes
    code_mapping = {
        400: "validation_error",
        404: "not_found",
        500: "internal_error",
        504: "timeout",
    }

    error_code = code_mapping.get(exc.status_code, "internal_error")

    error_response = ErrorEnvelope(
        error=ErrorInfo(code=error_code, message=str(exc.detail), trace_id=request_id)
    )

    return JSONResponse(status_code=exc.status_code, content=error_response.model_dump())


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    request_id = getattr(request.state, "request_id", "unknown")

    error_response = ErrorEnvelope(
        error=ErrorInfo(
            code="internal_error", message="An internal error occurred", trace_id=request_id
        )
    )

    return JSONResponse(status_code=500, content=error_response.model_dump())


# API Routes
@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, req: Request) -> ChatResponse:
    """Chat endpoint for debate conversations."""
    request_id = getattr(req.state, "request_id", "unknown")

    # Get chat handler from app state or global, initialize if needed
    handler = getattr(app.state, "chat_handler", None) or chat_handler

    if handler is None:
        try:
            # Initialize dependencies if not done yet (useful for testing)
            store_instance, handler_instance = initialize_dependencies()
            handler = handler_instance

            # Also set in app state for future requests
            app.state.store = store_instance
            app.state.chat_handler = handler_instance
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": {
                        "code": "initialization_error",
                        "message": f"Failed to initialize chat handler: {str(e)}",
                        "trace_id": request_id,
                    }
                },
            )

    if handler is None:
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "internal_error",
                    "message": "Chat handler not initialized",
                    "trace_id": request_id,
                }
            },
        )

    try:
        response = await handler.handle_chat(request, request_id)
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "internal_error",
                    "message": f"Chat processing failed: {str(e)}",
                    "trace_id": request_id,
                }
            },
        )


# Health endpoints
@app.get("/healthz")
async def liveness_check():
    """Liveness probe - returns 200 if process is alive."""
    return {"status": "ok"}


@app.get("/readyz", response_model=HealthResponse)
async def readiness_check():
    """Readiness probe - checks dependencies and shows version info."""
    response_data = {"status": "ok"}

    # Add version information
    git_hash = get_git_hash()
    version_info = {}
    if git_hash:
        version_info["git_hash"] = git_hash
    version_info["app_env"] = APP_ENV
    response_data["version"] = version_info

    # Get store from app state or global, initialize if needed
    current_store = getattr(app.state, "store", None) or store

    if current_store is None:
        # Initialize dependencies if not done yet (useful for testing)
        current_store, _ = initialize_dependencies()

    # Check Redis if we have a RedisStore (REDIS_URL configured and store is Redis)
    if REDIS_URL and current_store and hasattr(current_store, "redis"):
        try:
            redis_healthy = await current_store.health_check()
            response_data["deps"] = {"redis": "ok" if redis_healthy else "down"}

            if not redis_healthy:
                response_data["status"] = "degraded"
        except Exception:
            response_data["deps"] = {"redis": "down"}
            response_data["status"] = "degraded"

    return HealthResponse(**response_data)


# Optional metrics endpoint
if ENABLE_METRICS:

    @app.get("/metrics")
    async def metrics_endpoint():
        """Prometheus metrics endpoint."""
        content = metrics.get_metrics()
        if content is None:
            raise HTTPException(status_code=404, detail="Metrics not enabled")

        content_type = metrics.get_content_type()
        return PlainTextResponse(content, media_type=content_type)


# Root redirect
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Chat API",
        "version": "1.0.0",
        "endpoints": ["/api/v1/chat", "/healthz", "/readyz"],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.main:app", host="0.0.0.0", port=PORT, reload=APP_ENV == "local")
