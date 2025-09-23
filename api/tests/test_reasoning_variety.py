"""Tests for reasoning phrase variety and rotation."""
import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestReasoningVariety:
    """Test that reasoning and closing phrases don't repeat consecutively."""

    def test_closing_phrase_rotation(self, client):
        """Test that closing phrases rotate and don't repeat over 3 turns."""
        # Start conversation
        response1 = client.post(
            "/api/v1/chat",
            json={"message": "Technology will revolutionize education completely"}
        )

        conv_id = response1.json()["conversation_id"]
        message1 = response1.json()["message"][-1]["message"]

        # Continue for 2 more exchanges
        response2 = client.post(
            "/api/v1/chat",
            json={"conversation_id": conv_id, "message": "AI tutors will replace human teachers"}
        )
        message2 = response2.json()["message"][-1]["message"]

        response3 = client.post(
            "/api/v1/chat",
            json={"conversation_id": conv_id, "message": "Digital classrooms are the future"}
        )
        message3 = response3.json()["message"][-1]["message"]

        # Extract closing phrases (typically the last sentence)
        messages = [message1, message2, message3]
        closing_phrases = []

        for msg in messages:
            sentences = msg.split('.')
            if len(sentences) > 1:
                # Get last meaningful sentence
                last_sentence = sentences[-2].strip() if sentences[-1].strip() == '' else sentences[-1].strip()
                closing_phrases.append(last_sentence.lower())

        # No consecutive identical closing phrases
        for i in range(len(closing_phrases) - 1):
            assert closing_phrases[i] != closing_phrases[i + 1], f"Consecutive identical closing phrases: '{closing_phrases[i]}' and '{closing_phrases[i + 1]}'"

        print(f"Closing phrases: {closing_phrases}")  # For debugging

        # Should have different phrases
        unique_phrases = set(closing_phrases)
        assert len(unique_phrases) >= 2, f"Should have at least 2 different closing phrases, got: {closing_phrases}"

    def test_reasoning_phrase_variety(self, client):
        """Test that reasoning phrases within arguments show variety."""
        # Start conversation
        response1 = client.post(
            "/api/v1/chat",
            json={"message": "Climate change is the most important issue of our time"}
        )

        conv_id = response1.json()["conversation_id"]
        message1 = response1.json()["message"][-1]["message"]

        # Continue conversation
        response2 = client.post(
            "/api/v1/chat",
            json={"conversation_id": conv_id, "message": "We need immediate action on carbon emissions"}
        )
        message2 = response2.json()["message"][-1]["message"]

        response3 = client.post(
            "/api/v1/chat",
            json={"conversation_id": conv_id, "message": "Renewable energy is crucial for our future"}
        )
        message3 = response3.json()["message"][-1]["message"]

        messages = [message1, message2, message3]

        # Check for reasoning phrase variety
        reasoning_patterns = [
            "evidence strongly supports", "research confirms", "data indicates",
            "studies demonstrate", "analysis validates", "evidence substantiates"
        ]

        found_patterns = []
        for msg in messages:
            msg_lower = msg.lower()
            for pattern in reasoning_patterns:
                if pattern in msg_lower:
                    found_patterns.append(pattern)

        # Should not repeat the same reasoning phrase consecutively
        consecutive_repeats = 0
        for i in range(len(found_patterns) - 1):
            if found_patterns[i] == found_patterns[i + 1]:
                consecutive_repeats += 1

        assert consecutive_repeats == 0, f"Found consecutive reasoning phrase repeats: {found_patterns}"

        # Should use at least 2 different reasoning patterns across 3 messages
        unique_patterns = set(found_patterns)
        assert len(unique_patterns) >= 2, f"Should have reasoning variety, got: {found_patterns}"

    def test_spanish_phrase_rotation(self, client):
        """Test phrase rotation works in Spanish."""
        # Start Spanish conversation
        response1 = client.post(
            "/api/v1/chat",
            json={"message": "La inteligencia artificial transformará completamente la medicina"}
        )

        conv_id = response1.json()["conversation_id"]
        message1 = response1.json()["message"][-1]["message"]

        # Continue conversation
        response2 = client.post(
            "/api/v1/chat",
            json={"conversation_id": conv_id, "message": "Los robots médicos serán más precisos que los humanos"}
        )
        message2 = response2.json()["message"][-1]["message"]

        response3 = client.post(
            "/api/v1/chat",
            json={"conversation_id": conv_id, "message": "El diagnóstico automático salvará millones de vidas"}
        )
        message3 = response3.json()["message"][-1]["message"]

        # Check for Spanish reasoning phrase variety
        spanish_reasoning = [
            "evidencia respalda claramente", "investigación confirma", "datos indican",
            "estudios demuestran", "análisis valida", "evidencia sustenta"
        ]

        messages = [message1, message2, message3]
        found_spanish_patterns = []

        for msg in messages:
            msg_lower = msg.lower()
            for pattern in spanish_reasoning:
                if pattern in msg_lower:
                    found_spanish_patterns.append(pattern)

        # Should have variety in Spanish reasoning phrases
        if len(found_spanish_patterns) >= 2:
            unique_spanish = set(found_spanish_patterns)
            assert len(unique_spanish) >= 2, f"Should have Spanish reasoning variety: {found_spanish_patterns}"

    def test_deterministic_selection(self, client):
        """Test that phrase selection remains deterministic."""
        # Same input should produce same output
        message_text = "Technology is the key to solving world hunger"

        response1 = client.post("/api/v1/chat", json={"message": message_text})
        response2 = client.post("/api/v1/chat", json={"message": message_text})

        bot_message1 = response1.json()["message"][-1]["message"]
        bot_message2 = response2.json()["message"][-1]["message"]

        # Should be identical (deterministic)
        assert bot_message1 == bot_message2, f"Responses should be deterministic:\nResponse1: {bot_message1}\nResponse2: {bot_message2}"

    def test_phrase_pools_sufficient_size(self, client):
        """Test that we have sufficient phrase variety in pools."""
        # Start a longer conversation to test phrase pool depth
        response = client.post(
            "/api/v1/chat",
            json={"message": "Education technology will replace traditional learning"}
        )

        conv_id = response.json()["conversation_id"]
        messages = [response.json()["message"][-1]["message"]]

        # Continue for several turns
        follow_ups = [
            "Online courses are more effective than classroom learning",
            "Virtual reality will revolutionize educational experiences",
            "AI tutoring systems provide personalized learning paths",
            "Digital assessments are more accurate than traditional tests",
            "Remote learning eliminates geographical barriers"
        ]

        for follow_up in follow_ups:
            resp = client.post(
                "/api/v1/chat",
                json={"conversation_id": conv_id, "message": follow_up}
            )
            messages.append(resp.json()["message"][-1]["message"])

        # Extract all closing phrases
        all_closings = []
        for msg in messages:
            sentences = msg.split('.')
            if len(sentences) > 1:
                last_sentence = sentences[-2].strip() if sentences[-1].strip() == '' else sentences[-1].strip()
                all_closings.append(last_sentence.lower())

        # Should have good variety across 6 messages
        unique_closings = set(all_closings)
        variety_ratio = len(unique_closings) / len(all_closings)

        assert variety_ratio >= 0.5, f"Should have good closing variety, got {variety_ratio}: {all_closings}"

    def test_no_immediate_repetition_unconventional_topic(self, client):
        """Test phrase rotation works for unconventional topics too."""
        # Start unconventional topic conversation
        response1 = client.post(
            "/api/v1/chat",
            json={"message": "Wearing mismatched shoes is a bold fashion statement"}
        )

        conv_id = response1.json()["conversation_id"]
        message1 = response1.json()["message"][-1]["message"]

        response2 = client.post(
            "/api/v1/chat",
            json={"conversation_id": conv_id, "message": "It shows creativity and individuality"}
        )
        message2 = response2.json()["message"][-1]["message"]

        response3 = client.post(
            "/api/v1/chat",
            json={"conversation_id": conv_id, "message": "Fashion rules are meant to be broken"}
        )
        message3 = response3.json()["message"][-1]["message"]

        # Extract closing phrases
        messages = [message1, message2, message3]
        closings = []

        for msg in messages:
            sentences = msg.split('.')
            if len(sentences) > 1:
                last_sentence = sentences[-2].strip() if sentences[-1].strip() == '' else sentences[-1].strip()
                closings.append(last_sentence.lower())

        # No consecutive identical closings
        for i in range(len(closings) - 1):
            assert closings[i] != closings[i + 1], f"Consecutive identical closings in unconventional topic: {closings}"
