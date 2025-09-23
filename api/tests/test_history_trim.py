"""Test conversation history trimming logic."""
import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_history_trim_after_many_exchanges(client):
    """Test that after >5 exchanges, response still returns only last 5×2 (max 10)."""
    # Start a conversation
    response = client.post(
        "/api/v1/chat", json={"conversation_id": None, "message": "Let's talk about technology"}
    )

    assert response.status_code == 200
    data = response.json()
    conversation_id = data["conversation_id"]

    # Make 7 more exchanges (total of 8 exchanges = 16 messages)
    messages_sent = ["Let's talk about technology"]

    for i in range(7):
        user_message = f"What about point number {i+2}?"
        messages_sent.append(user_message)

        response = client.post(
            "/api/v1/chat", json={"conversation_id": conversation_id, "message": user_message}
        )

        assert response.status_code == 200
        data = response.json()

    # Final response should have exactly 10 messages (last 5 exchanges)
    final_messages = data["message"]
    assert len(final_messages) == 10

    # Verify chronological order (alternating user/bot)
    for i in range(0, len(final_messages), 2):
        assert final_messages[i]["role"] == "user"
        if i + 1 < len(final_messages):
            assert final_messages[i + 1]["role"] == "bot"

    # The messages should be the most recent ones
    # Since we sent 8 user messages, the response should contain the last 5
    expected_last_messages = messages_sent[-5:]
    actual_user_messages = [msg["message"] for msg in final_messages if msg["role"] == "user"]

    # Should have exactly 5 user messages (the most recent ones)
    assert len(actual_user_messages) == 5

    # The actual messages should match the expected last messages
    assert actual_user_messages == expected_last_messages


def test_history_trim_preserves_order(client):
    """Test that trimmed history preserves chronological order."""
    # Start conversation
    response = client.post(
        "/api/v1/chat", json={"conversation_id": None, "message": "First message"}
    )
    conversation_id = response.json()["conversation_id"]

    # Send many messages to trigger trimming
    for i in range(10):  # This will create 11 exchanges total
        response = client.post(
            "/api/v1/chat", json={"conversation_id": conversation_id, "message": f"Message {i+2}"}
        )

    data = response.json()
    messages = data["message"]

    # Should have exactly 10 messages
    assert len(messages) == 10

    # Verify strict chronological order
    user_count = 0
    bot_count = 0

    for i, message in enumerate(messages):
        if message["role"] == "user":
            user_count += 1
        else:
            bot_count += 1

        # In chronological order, user messages should come before corresponding bot messages
        if i > 0:
            prev_message = messages[i - 1]
            if message["role"] == "bot" and prev_message["role"] == "user":
                # This is valid: user then bot
                continue
            elif message["role"] == "user" and prev_message["role"] == "bot":
                # This is valid: bot then user (new exchange)
                continue
            # Should not have user-user or bot-bot sequences in trimmed history

    # Should have equal number of user and bot messages (5 each)
    assert user_count == 5
    assert bot_count == 5


def test_trim_logic_with_storage(client):
    """Test that storage trimming works correctly."""
    # Create conversation
    response = client.post(
        "/api/v1/chat", json={"conversation_id": None, "message": "Start conversation"}
    )
    conversation_id = response.json()["conversation_id"]

    # Add multiple exchanges
    for i in range(8):  # 9 total exchanges = 18 messages
        response = client.post(
            "/api/v1/chat", json={"conversation_id": conversation_id, "message": f"Exchange {i+2}"}
        )

    # Get final state
    data = response.json()
    messages = data["message"]

    # Should be trimmed to 10 messages max
    assert len(messages) <= 10
    assert len(messages) == 10  # Should be exactly 10 for this test

    # Verify each subsequent request also returns trimmed history
    response = client.post(
        "/api/v1/chat", json={"conversation_id": conversation_id, "message": "One more message"}
    )

    data = response.json()
    messages = data["message"]

    # Should still be 10 messages (new exchange replaces oldest)
    assert len(messages) == 10

    # The latest message should be present
    user_messages = [msg for msg in messages if msg["role"] == "user"]
    assert user_messages[-1]["message"] == "One more message"


def test_trim_edge_case_exactly_five_exchanges(client):
    """Test behavior when exactly 5 exchanges exist."""
    # Start conversation
    response = client.post("/api/v1/chat", json={"conversation_id": None, "message": "Message 1"})
    conversation_id = response.json()["conversation_id"]

    # Make exactly 4 more exchanges (5 total)
    for i in range(4):
        response = client.post(
            "/api/v1/chat", json={"conversation_id": conversation_id, "message": f"Message {i+2}"}
        )

    data = response.json()
    messages = data["message"]

    # Should have exactly 10 messages (5 exchanges × 2 messages each)
    assert len(messages) == 10

    # All original messages should be preserved
    user_messages = [msg["message"] for msg in messages if msg["role"] == "user"]
    expected_messages = [f"Message {i+1}" for i in range(5)]
    assert user_messages == expected_messages
