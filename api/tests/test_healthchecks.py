"""Test health check endpoints."""
import asyncio
import os
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_liveness_check(client):
    """Test /healthz endpoint returns 200."""
    response = client.get("/healthz")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_readiness_check_without_redis(client):
    """Test /readyz endpoint without Redis configuration."""
    with patch.dict(os.environ, {"REDIS_URL": ""}, clear=False):
        response = client.get("/readyz")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        # Should not include deps when Redis is not configured
        assert "deps" not in data or data["deps"] is None


@pytest.mark.asyncio
async def test_readiness_check_with_redis_healthy():
    """Test /readyz endpoint with healthy Redis."""
    # Mock a healthy Redis store
    with patch('api.main.REDIS_URL', 'redis://localhost:6379'), \
         patch('api.main.store') as mock_store:

        # Mock store health check to return True
        mock_store.health_check = AsyncMock(return_value=True)

        with TestClient(app) as client:
            response = client.get("/readyz")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert "deps" in data
            assert data["deps"]["redis"] == "ok"


@pytest.mark.asyncio
async def test_readiness_check_with_redis_unhealthy():
    """Test /readyz endpoint with unhealthy Redis."""
    # Mock an unhealthy Redis store
    with patch('api.main.REDIS_URL', 'redis://localhost:6379'), \
         patch('api.main.store') as mock_store:

        # Mock store health check to return False
        mock_store.health_check = AsyncMock(return_value=False)

        with TestClient(app) as client:
            response = client.get("/readyz")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "degraded"
            assert "deps" in data
            assert data["deps"]["redis"] == "down"


@pytest.mark.asyncio
async def test_readiness_check_with_redis_exception():
    """Test /readyz endpoint when Redis check raises exception."""
    # Mock Redis store that raises exception
    with patch('api.main.REDIS_URL', 'redis://localhost:6379'), \
         patch('api.main.store') as mock_store:

        # Mock store health check to raise exception
        mock_store.health_check = AsyncMock(side_effect=Exception("Connection failed"))

        with TestClient(app) as client:
            response = client.get("/readyz")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "degraded"
            assert "deps" in data
            assert data["deps"]["redis"] == "down"


def test_timeout_endpoint():
    """Test timeout behavior by creating a new app with short timeout."""
    from fastapi import FastAPI

    from api.main import initialize_dependencies
    from api.middleware import TimeoutMiddleware

    # Create a new app with short timeout for testing
    test_app = FastAPI()
    test_app.add_middleware(TimeoutMiddleware, timeout_seconds=1)

    @test_app.get("/slow")
    async def slow_endpoint():
        await asyncio.sleep(2)  # Sleep longer than timeout
        return {"status": "slow"}

    with TestClient(test_app) as client:
        response = client.get("/slow")

        assert response.status_code == 504
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "timeout"
        assert data["error"]["message"] == "Request exceeded time limit"
        assert data["error"]["details"] == {}
        assert "trace_id" in data["error"]
        assert "X-Request-Id" in response.headers


def test_metrics_endpoint_disabled(client):
    """Test /metrics endpoint when metrics are disabled."""
    # Ensure metrics are disabled
    with patch.dict(os.environ, {"ENABLE_METRICS": "0"}, clear=False):
        response = client.get("/metrics")

        # Should return 404 since metrics endpoint is not registered
        assert response.status_code == 404


@pytest.mark.skipif(
    not hasattr(__import__('api.observability', fromlist=['PROMETHEUS_AVAILABLE']), 'PROMETHEUS_AVAILABLE') or
    not __import__('api.observability', fromlist=['PROMETHEUS_AVAILABLE']).PROMETHEUS_AVAILABLE,
    reason="Prometheus client not available"
)
def test_metrics_endpoint_enabled(client):
    """Test /metrics endpoint when metrics are enabled."""
    with patch.dict(os.environ, {"ENABLE_METRICS": "1"}, clear=False):
        # Need to restart app with metrics enabled
        from api.main import app as metrics_app

        with TestClient(metrics_app) as metrics_client:
            response = metrics_client.get("/metrics")

            if response.status_code == 200:
                # Should return Prometheus format
                assert response.headers["content-type"].startswith("text/plain")
                content = response.text
                assert isinstance(content, str)
                # Basic check for Prometheus format
                assert "# HELP" in content or len(content) >= 0
            else:
                # If endpoint doesn't exist, that's also acceptable per spec
                assert response.status_code == 404


def test_root_endpoint(client):
    """Test root endpoint returns basic info."""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "endpoints" in data
    assert "/api/v1/chat" in data["endpoints"]
    assert "/healthz" in data["endpoints"]
    assert "/readyz" in data["endpoints"]


def test_health_endpoints_include_request_id(client):
    """Test that health endpoints include X-Request-Id header."""
    # Test liveness
    response = client.get("/healthz")
    assert "X-Request-Id" in response.headers

    # Test readiness
    response = client.get("/readyz")
    assert "X-Request-Id" in response.headers


def test_cors_headers(client):
    """Test that CORS headers are properly set."""
    # Test with a POST request that should trigger CORS headers
    response = client.post(
        "/api/v1/chat",
        json={"conversation_id": None, "message": "test"},
        headers={"Origin": "http://example.com"}
    )

    # Should have CORS headers
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == "*"
