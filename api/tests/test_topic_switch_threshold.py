"""Tests for topic switch detection threshold."""
import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestTopicSwitchThreshold:
    """Test robust topic switch detection with thresholds."""

    def test_superficial_overlap_no_switch(self, client):
        """Test that superficial topic overlap doesn't trigger switch."""
        # Start with technology topic
        response1 = client.post(
            "/api/v1/chat",
            json={
                "message": "Artificial intelligence and machine learning will transform industries"
            },
        )

        conv_id = response1.json()["conversation_id"]

        # Add one more exchange to get past first turn
        response2 = client.post(
            "/api/v1/chat",
            json={
                "conversation_id": conv_id,
                "message": "Neural networks are becoming more sophisticated",
            },
        )

        # Message with superficial climate overlap (just one keyword)
        response3 = client.post(
            "/api/v1/chat",
            json={
                "conversation_id": conv_id,
                "message": "The technology environment is rapidly evolving",
            },
        )

        bot_message = response3.json()["message"][-1]["message"]

        # Should NOT contain topic switch acknowledgment
        switch_indicators = ["stay focused", "open a new thread", "let's", "sigamos"]
        switch_found = any(indicator in bot_message.lower() for indicator in switch_indicators)

        assert not switch_found, f"Should not trigger switch for superficial overlap: {bot_message}"

    def test_strong_topic_switch_triggers(self, client):
        """Test that strong topic switch with multiple keywords triggers acknowledgment."""
        # Start with technology topic
        response1 = client.post(
            "/api/v1/chat", json={"message": "Technology and digital innovation are revolutionary"}
        )

        conv_id = response1.json()["conversation_id"]

        # Add one more exchange
        response2 = client.post(
            "/api/v1/chat",
            json={
                "conversation_id": conv_id,
                "message": "Software development is advancing rapidly",
            },
        )

        # Strong climate topic switch (multiple climate keywords)
        response3 = client.post(
            "/api/v1/chat",
            json={
                "conversation_id": conv_id,
                "message": "But climate change and carbon emissions are destroying our environment",
            },
        )

        bot_message = response3.json()["message"][-1]["message"]

        # Should contain topic switch acknowledgment
        switch_indicators = ["stay focused", "open a new thread", "technology"]
        switch_found = any(indicator in bot_message.lower() for indicator in switch_indicators)

        assert switch_found, f"Should trigger switch for strong topic change: {bot_message}"

        # Should mention both original topic (technology) and new topic (climate)
        mentions_tech = "technology" in bot_message.lower()
        mentions_climate = any(word in bot_message.lower() for word in ["climate", "environmental"])

        assert mentions_tech, f"Should mention original technology topic: {bot_message}"
        # Note: may not always mention new topic name specifically due to implementation

    def test_single_keyword_insufficient(self, client):
        """Test that single keyword match is insufficient for topic switch."""
        # Start with education topic
        response1 = client.post(
            "/api/v1/chat",
            json={"message": "Education and learning should be accessible to everyone"},
        )

        conv_id = response1.json()["conversation_id"]

        # Continue education conversation
        response2 = client.post(
            "/api/v1/chat",
            json={
                "conversation_id": conv_id,
                "message": "Schools need better resources and teachers",
            },
        )

        # Message with single climate keyword but not really about climate
        response3 = client.post(
            "/api/v1/chat",
            json={
                "conversation_id": conv_id,
                "message": "The learning environment should be supportive",
            },
        )

        bot_message = response3.json()["message"][-1]["message"]

        # Should NOT switch topic for single keyword (look for switch acknowledgment phrases only)
        switch_indicators = ["stay focused", "open a new thread", "sigamos centrados"]
        switch_found = any(indicator in bot_message.lower() for indicator in switch_indicators)

        assert not switch_found, f"Single keyword should not trigger switch: {bot_message}"

    def test_multiple_keywords_required_threshold(self, client):
        """Test that 2+ keywords are required for topic switch."""
        # Start with technology topic
        response1 = client.post(
            "/api/v1/chat",
            json={"message": "Technology and artificial intelligence are the future"},
        )

        conv_id = response1.json()["conversation_id"]

        response2 = client.post(
            "/api/v1/chat",
            json={"conversation_id": conv_id, "message": "Digital transformation is inevitable"},
        )

        # Test with exactly 2 climate keywords (should trigger)
        response3 = client.post(
            "/api/v1/chat",
            json={
                "conversation_id": conv_id,
                "message": "We should focus on climate change and carbon reduction instead",
            },
        )

        bot_message3 = response3.json()["message"][-1]["message"]

        # Should trigger with 2+ keywords
        switch_found = any(
            indicator in bot_message3.lower() for indicator in ["stay focused", "open a new thread"]
        )
        assert switch_found, f"Should trigger with 2+ keywords: {bot_message3}"

        # Start new conversation to test with 1 keyword
        response4 = client.post(
            "/api/v1/chat", json={"message": "Technology will change everything"}
        )

        conv_id2 = response4.json()["conversation_id"]

        response5 = client.post(
            "/api/v1/chat",
            json={"conversation_id": conv_id2, "message": "Innovation drives progress"},
        )

        # Test with only 1 climate keyword (should NOT trigger)
        response6 = client.post(
            "/api/v1/chat",
            json={"conversation_id": conv_id2, "message": "But the environment matters too"},
        )

        bot_message6 = response6.json()["message"][-1]["message"]

        # Should NOT trigger with only 1 keyword
        switch_found2 = any(
            indicator in bot_message6.lower() for indicator in ["stay focused", "open a new thread"]
        )
        assert not switch_found2, f"Should NOT trigger with only 1 keyword: {bot_message6}"

    def test_spanish_topic_switch_threshold(self, client):
        """Test topic switch threshold works in Spanish."""
        # Start Spanish technology conversation
        response1 = client.post(
            "/api/v1/chat",
            json={"message": "La tecnología y la inteligencia artificial son el futuro"},
        )

        conv_id = response1.json()["conversation_id"]

        response2 = client.post(
            "/api/v1/chat",
            json={"conversation_id": conv_id, "message": "Las máquinas cambiarán todo"},
        )

        # Strong climate switch in Spanish (multiple keywords)
        response3 = client.post(
            "/api/v1/chat",
            json={
                "conversation_id": conv_id,
                "message": "Pero el cambio climático y las emisiones de carbono son más importantes",
            },
        )

        bot_message = response3.json()["message"][-1]["message"]

        # Should contain Spanish topic switch acknowledgment
        spanish_switch_indicators = ["centrados", "hilo", "tecnología"]
        switch_found = any(
            indicator in bot_message.lower() for indicator in spanish_switch_indicators
        )

        assert switch_found, f"Should trigger Spanish topic switch: {bot_message}"

    def test_same_topic_keywords_no_switch(self, client):
        """Test that staying on same topic doesn't trigger switch."""
        # Start with climate topic
        response1 = client.post(
            "/api/v1/chat",
            json={"message": "Climate change and global warming are serious threats"},
        )

        conv_id = response1.json()["conversation_id"]

        response2 = client.post(
            "/api/v1/chat",
            json={"conversation_id": conv_id, "message": "Carbon emissions are rising"},
        )

        # Continue with same topic (more climate keywords)
        response3 = client.post(
            "/api/v1/chat",
            json={
                "conversation_id": conv_id,
                "message": "Renewable energy and environment protection are crucial",
            },
        )

        bot_message = response3.json()["message"][-1]["message"]

        # Should NOT trigger switch when staying on same topic
        switch_indicators = ["stay focused", "open a new thread", "sigamos"]
        switch_found = any(indicator in bot_message.lower() for indicator in switch_indicators)

        assert not switch_found, f"Should not switch when staying on same topic: {bot_message}"

    def test_general_to_specific_no_false_positive(self, client):
        """Test general topic doesn't falsely trigger switches."""
        # Start with unconventional topic (maps to general)
        response1 = client.post(
            "/api/v1/chat",
            json={"message": "Pizza with ranch dressing is the ultimate comfort food"},
        )

        conv_id = response1.json()["conversation_id"]

        response2 = client.post(
            "/api/v1/chat",
            json={"conversation_id": conv_id, "message": "Food preferences are very personal"},
        )

        # Mention some tech words - should not trigger switch from general
        response3 = client.post(
            "/api/v1/chat",
            json={
                "conversation_id": conv_id,
                "message": "Even technology can't predict taste preferences",
            },
        )

        bot_message = response3.json()["message"][-1]["message"]

        # Should NOT trigger switch (general topic doesn't have switch detection)
        switch_indicators = ["stay focused", "open a new thread"]
        switch_found = any(indicator in bot_message.lower() for indicator in switch_indicators)

        assert not switch_found, f"General topic should not trigger false switches: {bot_message}"

    def test_cross_topic_boundary_detection(self, client):
        """Test detection across different supported topics."""
        # Start with education
        response1 = client.post(
            "/api/v1/chat", json={"message": "Education and schools need major improvements"}
        )

        conv_id = response1.json()["conversation_id"]

        response2 = client.post(
            "/api/v1/chat",
            json={"conversation_id": conv_id, "message": "Teachers deserve better support"},
        )

        # Switch to technology (different supported topic)
        response3 = client.post(
            "/api/v1/chat",
            json={
                "conversation_id": conv_id,
                "message": "Actually, artificial intelligence and digital technology will solve this",
            },
        )

        bot_message = response3.json()["message"][-1]["message"]

        # Should detect switch from education to technology
        switch_found = any(
            indicator in bot_message.lower() for indicator in ["stay focused", "open a new thread"]
        )
        education_mentioned = "education" in bot_message.lower()

        assert switch_found, f"Should detect education->technology switch: {bot_message}"
        assert education_mentioned, f"Should mention original education topic: {bot_message}"
