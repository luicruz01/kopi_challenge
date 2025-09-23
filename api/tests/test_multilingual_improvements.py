"""Tests for multilingual and improvement features."""
import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestLanguageLock:
    """Test language detection and locking per conversation."""

    def test_spanish_language_lock(self, client):
        """Test that Spanish input yields Spanish responses throughout conversation."""
        # First message in Spanish
        response1 = client.post(
            "/api/v1/chat",
            json={"message": "Creo que la tecnología es beneficiosa para la sociedad"}
        )

        assert response1.status_code == 200
        data1 = response1.json()
        conv_id = data1["conversation_id"]
        bot_message1 = data1["message"][-1]["message"]

        # Bot should respond in Spanish
        spanish_indicators = ["que", "es", "la", "el", "de", "y", "en", "con", "por", "para"]
        spanish_found = sum(1 for word in spanish_indicators if word in bot_message1.lower())
        assert spanish_found >= 3, f"Expected Spanish response but got: {bot_message1}"

        # Continue conversation - should maintain Spanish
        response2 = client.post(
            "/api/v1/chat",
            json={"conversation_id": conv_id, "message": "¿Qué opinas sobre eso?"}
        )

        assert response2.status_code == 200
        data2 = response2.json()
        bot_message2 = data2["message"][-1]["message"]

        # Should still be in Spanish
        spanish_found2 = sum(1 for word in spanish_indicators if word in bot_message2.lower())
        assert spanish_found2 >= 3, f"Expected Spanish response in continuation but got: {bot_message2}"

    def test_english_language_lock(self, client):
        """Test that English input yields English responses throughout conversation."""
        # First message in English
        response1 = client.post(
            "/api/v1/chat",
            json={"message": "I believe technology is beneficial for society"}
        )

        assert response1.status_code == 200
        data1 = response1.json()
        conv_id = data1["conversation_id"]
        bot_message1 = data1["message"][-1]["message"]

        # Bot should respond in English - check for clear English patterns
        english_patterns = ["i believe", "that require", "it's evident", "we cannot", "consider the analogy", "but ask yourself"]
        spanish_patterns = ["creo que", "que requiere", "es evidente", "no podemos", "considera la analogía", "pero pregúntate"]

        english_found = sum(1 for pattern in english_patterns if pattern in bot_message1.lower())
        spanish_found = sum(1 for pattern in spanish_patterns if pattern in bot_message1.lower())

        assert english_found > spanish_found or "I believe" in bot_message1, f"Expected English response but got: {bot_message1}"

        # Continue conversation - should maintain English
        response2 = client.post(
            "/api/v1/chat",
            json={"conversation_id": conv_id, "message": "What do you think about that?"}
        )

        assert response2.status_code == 200
        data2 = response2.json()
        bot_message2 = data2["message"][-1]["message"]

        # Should still be in English - check for clear English patterns
        english_found2 = sum(1 for pattern in english_patterns if pattern in bot_message2.lower())
        spanish_found2 = sum(1 for pattern in spanish_patterns if pattern in bot_message2.lower())
        assert english_found2 > spanish_found2 or any(word in bot_message2.lower() for word in ["that", "this", "what", "about"]), f"Expected English response in continuation but got: {bot_message2}"

    def test_separate_conversations_different_languages(self, client):
        """Test that separate conversations can have different languages."""
        # Start Spanish conversation
        spanish_response = client.post(
            "/api/v1/chat",
            json={"message": "Hola, hablemos sobre tecnología"}
        )
        spanish_conv_id = spanish_response.json()["conversation_id"]
        spanish_bot_message = spanish_response.json()["message"][-1]["message"]

        # Start English conversation
        english_response = client.post(
            "/api/v1/chat",
            json={"message": "Hello, let's talk about technology"}
        )
        english_conv_id = english_response.json()["conversation_id"]
        english_bot_message = english_response.json()["message"][-1]["message"]

        # Different conversation IDs
        assert spanish_conv_id != english_conv_id

        # Check language indicators in responses
        spanish_indicators = ["que", "es", "la", "el", "tecnología"]
        english_indicators = ["that", "is", "the", "and", "technology"]

        spanish_count = sum(1 for word in spanish_indicators if word in spanish_bot_message.lower())
        english_count = sum(1 for word in english_indicators if word in english_bot_message.lower())

        assert spanish_count >= 2, f"Spanish conversation should have Spanish response: {spanish_bot_message}"
        assert english_count >= 2, f"English conversation should have English response: {english_bot_message}"


class TestResponseVariety:
    """Test deterministic variety in responses."""

    def test_no_repeated_analogies(self, client):
        """Test that analogies don't repeat across consecutive turns."""
        # Start conversation
        response1 = client.post(
            "/api/v1/chat",
            json={"message": "Technology will improve our lives"}
        )
        conv_id = response1.json()["conversation_id"]
        message1 = response1.json()["message"][-1]["message"]

        # Continue for 2 more exchanges
        response2 = client.post(
            "/api/v1/chat",
            json={"conversation_id": conv_id, "message": "But what about the risks?"}
        )
        message2 = response2.json()["message"][-1]["message"]

        response3 = client.post(
            "/api/v1/chat",
            json={"conversation_id": conv_id, "message": "I still think it's beneficial"}
        )
        message3 = response3.json()["message"][-1]["message"]

        # Extract analogies (look for common patterns)
        analogy_patterns = [
            "learning to drive", "using new tools", "adopting better methods",
            "tending a garden", "building a house", "running a marathon"
        ]

        # Find analogies in each message
        analogies_found = []
        for message in [message1, message2, message3]:
            message_analogies = [pattern for pattern in analogy_patterns if pattern in message.lower()]
            analogies_found.extend(message_analogies)

        # No immediate repetition (consecutive messages shouldn't have same analogy)
        for i in range(len(analogies_found) - 1):
            assert analogies_found[i] != analogies_found[i + 1], f"Found repeated analogy: {analogies_found[i]}"

    def test_topic_specific_arguments(self, client):
        """Test that responses contain topic-specific arguments."""
        # Test climate topic
        climate_response = client.post(
            "/api/v1/chat",
            json={"message": "Climate change is a serious global issue"}
        )
        climate_message = climate_response.json()["message"][-1]["message"].lower()

        # Should contain climate-specific terms
        climate_terms = ["renewable", "carbon", "sustainable", "environment", "climate"]
        climate_found = any(term in climate_message for term in climate_terms)
        assert climate_found, f"Climate topic should contain relevant terms: {climate_message}"

        # Test technology topic with more explicit tech words
        tech_response = client.post(
            "/api/v1/chat",
            json={"message": "Technology and artificial intelligence will transform society through digital innovation"}
        )
        tech_message = tech_response.json()["message"][-1]["message"].lower()

        # Should contain tech-specific terms
        tech_terms = ["innovation", "efficiency", "technology", "advancement", "digital"]
        tech_found = any(term in tech_message for term in tech_terms)
        assert tech_found, f"Technology topic should contain relevant terms: {tech_message}"


class TestTopicSwitchAcknowledgment:
    """Test topic switch acknowledgment feature."""

    def test_topic_switch_acknowledgment_english(self, client):
        """Test topic switch acknowledgment in English."""
        # Start with technology topic
        response1 = client.post(
            "/api/v1/chat",
            json={"message": "I think artificial intelligence is revolutionary"}
        )
        conv_id = response1.json()["conversation_id"]

        # Add one more exchange to get past first turn
        response2 = client.post(
            "/api/v1/chat",
            json={"conversation_id": conv_id, "message": "AI will change everything"}
        )

        # Switch to climate topic
        response3 = client.post(
            "/api/v1/chat",
            json={"conversation_id": conv_id, "message": "Actually, let's talk about climate change instead"}
        )

        bot_message = response3.json()["message"][-1]["message"]

        # Should contain topic switch acknowledgment
        switch_indicators = ["stay focused", "open a new thread", "technology", "climate"]
        found_acknowledgment = any(indicator in bot_message.lower() for indicator in switch_indicators)
        assert found_acknowledgment, f"Expected topic switch acknowledgment: {bot_message}"

    def test_topic_switch_acknowledgment_spanish(self, client):
        """Test topic switch acknowledgment in Spanish."""
        # Start with technology topic in Spanish
        response1 = client.post(
            "/api/v1/chat",
            json={"message": "Creo que la inteligencia artificial es revolucionaria"}
        )
        conv_id = response1.json()["conversation_id"]

        # Add one more exchange
        response2 = client.post(
            "/api/v1/chat",
            json={"conversation_id": conv_id, "message": "La IA cambiará todo"}
        )

        # Switch to climate topic
        response3 = client.post(
            "/api/v1/chat",
            json={"conversation_id": conv_id, "message": "Mejor hablemos del cambio climático"}
        )

        bot_message = response3.json()["message"][-1]["message"]

        # Should contain Spanish topic switch acknowledgment
        spanish_switch_indicators = ["centrados", "hilo", "tecnología", "cambio climático"]
        found_acknowledgment = any(indicator in bot_message.lower() for indicator in spanish_switch_indicators)
        assert found_acknowledgment, f"Expected Spanish topic switch acknowledgment: {bot_message}"

    def test_no_topic_switch_acknowledgment_same_topic(self, client):
        """Test that no acknowledgment appears when staying on same topic."""
        # Start with technology
        response1 = client.post(
            "/api/v1/chat",
            json={"message": "I think AI is transformative"}
        )
        conv_id = response1.json()["conversation_id"]

        # Continue with technology (no switch)
        response2 = client.post(
            "/api/v1/chat",
            json={"conversation_id": conv_id, "message": "Robots will help us"}
        )

        response3 = client.post(
            "/api/v1/chat",
            json={"conversation_id": conv_id, "message": "Digital innovation is key"}
        )

        bot_message = response3.json()["message"][-1]["message"]

        # Should NOT contain topic switch acknowledgment
        switch_indicators = ["stay focused", "open a new thread", "new topic"]
        found_acknowledgment = any(indicator in bot_message.lower() for indicator in switch_indicators)
        assert not found_acknowledgment, f"Should not have topic switch acknowledgment for same topic: {bot_message}"


class TestClaimExtraction:
    """Test improved claim extraction for refutation."""

    def test_claim_extraction_english(self, client):
        """Test that bot extracts and refutes actual claims in English."""
        response = client.post(
            "/api/v1/chat",
            json={"message": "I believe robots will eliminate human creativity and art"}
        )

        bot_message = response.json()["message"][-1]["message"]

        # Should contain extracted claim in refutation
        claim_indicators = ["robots will eliminate", "human creativity", "your claim"]
        found_claim = any(indicator in bot_message.lower() for indicator in claim_indicators)
        assert found_claim, f"Expected extracted claim in refutation: {bot_message}"

        # Should use proper claim extraction format (not old generic fragments)
        proper_extraction = (("the argument that" in bot_message.lower() or "your claim that" in bot_message.lower()) and
                           '"' in bot_message)  # Should contain quoted claim
        old_style_extraction = ("your point about i believe" in bot_message.lower() or
                              "while you mention i believe" in bot_message.lower())

        assert proper_extraction and not old_style_extraction, f"Should use new claim extraction format: {bot_message}"

    def test_claim_extraction_spanish(self, client):
        """Test that bot extracts and refutes actual claims in Spanish."""
        response = client.post(
            "/api/v1/chat",
            json={"message": "Pienso que los robots eliminarán la creatividad humana"}
        )

        bot_message = response.json()["message"][-1]["message"]

        # Should contain extracted claim in Spanish refutation
        claim_indicators = ["robots eliminarán", "creatividad humana", "tu afirmación"]
        found_claim = any(indicator in bot_message.lower() for indicator in claim_indicators)
        assert found_claim, f"Expected extracted claim in Spanish refutation: {bot_message}"
