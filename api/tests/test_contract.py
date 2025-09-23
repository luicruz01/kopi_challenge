"""Test API contract compliance."""
import uuid
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_chat_without_conversation_id(client):
    """Test POST without conversation_id returns UUID v4 and correct schema."""
    response = client.post(
        "/api/v1/chat",
        json={"conversation_id": None, "message": "I think climate change is not a big deal"}
    )

    assert response.status_code == 200
    data = response.json()

    # Check response structure
    assert "conversation_id" in data
    assert "message" in data

    # Validate UUID v4
    conversation_id = data["conversation_id"]
    uuid_obj = UUID(conversation_id)
    assert uuid_obj.version == 4

    # Check message array structure
    messages = data["message"]
    assert isinstance(messages, list)
    assert len(messages) == 2  # user + bot response

    # Check chronological order (user first, then bot)
    assert messages[0]["role"] == "user"
    assert messages[0]["message"] == "I think climate change is not a big deal"
    assert messages[1]["role"] == "bot"
    assert isinstance(messages[1]["message"], str)
    assert len(messages[1]["message"]) > 0

    # Check messages count ≤ 10
    assert len(messages) <= 10


def test_chat_with_conversation_id(client):
    """Test POST with existing conversation_id continues conversation."""
    # First request to create conversation
    response1 = client.post(
        "/api/v1/chat",
        json={"conversation_id": None, "message": "Technology is amazing"}
    )

    assert response1.status_code == 200
    data1 = response1.json()
    conversation_id = data1["conversation_id"]

    # Second request with existing conversation_id
    response2 = client.post(
        "/api/v1/chat",
        json={"conversation_id": conversation_id, "message": "What are the benefits?"}
    )

    assert response2.status_code == 200
    data2 = response2.json()

    # Should return same conversation_id
    assert data2["conversation_id"] == conversation_id

    # Should have 4 messages (2 from first exchange, 2 from second)
    messages = data2["message"]
    assert len(messages) == 4

    # Check chronological order
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "bot"
    assert messages[2]["role"] == "user"
    assert messages[3]["role"] == "bot"


def test_chat_invalid_conversation_id(client):
    """Test POST with invalid conversation_id returns 404."""
    fake_uuid = str(uuid.uuid4())

    response = client.post(
        "/api/v1/chat",
        json={"conversation_id": fake_uuid, "message": "Hello"}
    )

    assert response.status_code == 404
    data = response.json()

    # Check error envelope
    assert "error" in data
    assert data["error"]["code"] == "not_found"
    assert "trace_id" in data["error"]


def test_chat_message_too_large(client):
    """Test message size validation (4KB limit)."""
    large_message = "x" * 5000  # > 4KB

    response = client.post(
        "/api/v1/chat",
        json={"conversation_id": None, "message": large_message}
    )

    assert response.status_code == 422  # Validation error
    data = response.json()

    # Should contain validation error details
    assert "detail" in data


def test_chat_message_4kb_utf8_boundary(client):
    """Test 4KB UTF-8 boundary conditions."""
    # Test exactly 4KB (4096 bytes) with ASCII - should pass
    ascii_4kb = "a" * 4096
    response = client.post(
        "/api/v1/chat",
        json={"message": ascii_4kb}
    )
    assert response.status_code == 200, "Exactly 4KB ASCII should be accepted"

    # Test exactly 4KB (4096 bytes) with UTF-8 multibyte chars - should pass
    # Using 'é' (2 bytes in UTF-8) to create exactly 4KB
    utf8_char = "é"  # 2 bytes in UTF-8
    padding = "a" * (4096 - len(utf8_char.encode('utf-8')))  # Fill remaining bytes with ASCII
    utf8_4kb = utf8_char + padding

    # Verify it's exactly 4KB
    assert len(utf8_4kb.encode('utf-8')) == 4096, "UTF-8 message should be exactly 4096 bytes"

    response = client.post(
        "/api/v1/chat",
        json={"message": utf8_4kb}
    )
    assert response.status_code == 200, "Exactly 4KB UTF-8 should be accepted"

    # Test >4KB with multibyte characters - should fail
    # Using multiple 3-byte UTF-8 characters to exceed 4KB
    utf8_3byte = "€"  # 3 bytes in UTF-8
    over_4kb_utf8 = utf8_3byte * 1366  # 1366 * 3 = 4098 bytes > 4096

    # Verify it exceeds 4KB
    assert len(over_4kb_utf8.encode('utf-8')) > 4096, "UTF-8 message should exceed 4096 bytes"

    response = client.post(
        "/api/v1/chat",
        json={"message": over_4kb_utf8}
    )
    assert response.status_code == 422, "Messages >4KB should be rejected"


def test_chat_empty_message(client):
    """Test empty message validation."""
    response = client.post(
        "/api/v1/chat",
        json={"conversation_id": None, "message": ""}
    )

    # Should succeed with empty string (API accepts any string)
    # The engine will handle it appropriately
    assert response.status_code == 200


def test_response_headers(client):
    """Test response includes X-Request-Id header."""
    response = client.post(
        "/api/v1/chat",
        json={"conversation_id": None, "message": "Hello"}
    )

    assert response.status_code == 200
    assert "X-Request-Id" in response.headers

    # Should be valid UUID
    request_id = response.headers["X-Request-Id"]
    UUID(request_id)  # Will raise if invalid


def test_request_id_propagation(client):
    """Test X-Request-Id is echoed back when provided."""
    test_request_id = str(uuid.uuid4())

    response = client.post(
        "/api/v1/chat",
        json={"conversation_id": None, "message": "Hello"},
        headers={"X-Request-Id": test_request_id}
    )

    assert response.status_code == 200
    assert response.headers["X-Request-Id"] == test_request_id


def test_deterministic_responses(client):
    """Test that responses are deterministic for same input."""
    message = "Climate change is a serious issue"

    # Make same request multiple times
    responses = []
    for _ in range(3):
        response = client.post(
            "/api/v1/chat",
            json={"conversation_id": None, "message": message}
        )
        assert response.status_code == 200
        responses.append(response.json())

    # All bot responses should be identical (deterministic)
    bot_messages = [r["message"][1]["message"] for r in responses]
    assert bot_messages[0] == bot_messages[1] == bot_messages[2]
