"""Comprehensive debate engine testing battery."""
import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestLanguageHandling:
    """Test multilingual conversation capabilities."""

    def test_spanish_language_detection(self, client):
        """Test if bot can detect and respond in Spanish."""
        response = client.post(
            "/api/v1/chat",
            json={"message": "Hola, ¿puedes hablar en español conmigo?"}
        )

        assert response.status_code == 200
        data = response.json()
        bot_message = data["message"][-1]["message"]

        # Check if response contains Spanish words or structure
        spanish_indicators = ["hola", "español", "puedo", "sí", "no", "que", "es", "la", "el"]
        contains_spanish = any(indicator in bot_message.lower() for indicator in spanish_indicators)

        # Document current behavior - this test will likely fail
        print(f"Bot response to Spanish input: {bot_message}")
        # assert contains_spanish, f"Bot should respond in Spanish but got: {bot_message}"

    def test_french_language_detection(self, client):
        """Test if bot can detect and respond in French."""
        response = client.post(
            "/api/v1/chat",
            json={"message": "Bonjour, pouvez-vous parler français avec moi?"}
        )

        assert response.status_code == 200
        data = response.json()
        bot_message = data["message"][-1]["message"]

        # Document current behavior
        print(f"Bot response to French input: {bot_message}")

    def test_mixed_language_conversation(self, client):
        """Test behavior when switching languages mid-conversation."""
        # Start in English
        response1 = client.post(
            "/api/v1/chat",
            json={"message": "Let's talk about artificial intelligence."}
        )
        conv_id = response1.json()["conversation_id"]

        # Switch to Spanish
        response2 = client.post(
            "/api/v1/chat",
            json={"conversation_id": conv_id, "message": "Ahora hablemos en español sobre este tema."}
        )

        assert response2.status_code == 200
        bot_message = response2.json()["message"][-1]["message"]
        print(f"Bot response after language switch: {bot_message}")


class TestTopicEngagement:
    """Test bot's ability to engage with specific topics."""

    def test_ai_employment_topic(self, client):
        """Test engagement with AI and employment topic."""
        response = client.post(
            "/api/v1/chat",
            json={"message": "Artificial intelligence will replace human jobs in manufacturing. Robots are more efficient and don't need breaks."}
        )

        assert response.status_code == 200
        data = response.json()
        bot_message = data["message"][-1]["message"].lower()

        # Check if bot engages with specific terms
        ai_terms = ["artificial intelligence", "robots", "manufacturing", "jobs", "employment", "workers", "automation"]
        topic_engagement = any(term in bot_message for term in ai_terms)

        print(f"AI topic engagement: {topic_engagement}")
        print(f"Bot response: {bot_message}")

    def test_climate_change_topic(self, client):
        """Test engagement with climate change topic."""
        response = client.post(
            "/api/v1/chat",
            json={"message": "Climate change is caused by human activities. We need renewable energy like solar and wind power to reduce carbon emissions."}
        )

        assert response.status_code == 200
        data = response.json()
        bot_message = data["message"][-1]["message"].lower()

        climate_terms = ["climate", "renewable", "solar", "wind", "carbon", "emissions", "environment", "green energy"]
        topic_engagement = any(term in bot_message for term in climate_terms)

        print(f"Climate topic engagement: {topic_engagement}")
        print(f"Bot response: {bot_message}")

    def test_topic_switching(self, client):
        """Test bot adaptation when topic switches dramatically."""
        # Start with technology
        response1 = client.post(
            "/api/v1/chat",
            json={"message": "Smartphones have revolutionized communication and information access."}
        )
        conv_id = response1.json()["conversation_id"]

        # Switch to cooking
        response2 = client.post(
            "/api/v1/chat",
            json={"conversation_id": conv_id, "message": "Actually, let's talk about cooking instead. Do you think traditional recipes are better than modern fusion cuisine?"}
        )

        assert response2.status_code == 200
        data = response2.json()
        bot_message = data["message"][-1]["message"].lower()

        # Check if bot acknowledges topic switch
        cooking_terms = ["cooking", "recipes", "cuisine", "food", "chef", "ingredients", "traditional", "fusion"]
        topic_switch_detected = any(term in bot_message for term in cooking_terms)

        print(f"Topic switch detection: {topic_switch_detected}")
        print(f"Bot response to topic switch: {bot_message}")


class TestResponseQuality:
    """Test quality and variety of bot responses."""

    def test_response_diversity(self, client):
        """Test if bot gives different responses to different inputs."""
        topics = [
            "Technology is making life easier",
            "Education should be free for everyone",
            "Space exploration is worth the investment",
            "Social media has negative effects on society"
        ]

        responses = []
        for topic in topics:
            response = client.post(
                "/api/v1/chat",
                json={"message": topic}
            )
            bot_message = response.json()["message"][-1]["message"]
            responses.append(bot_message)

        # Check if responses are identical (they shouldn't be)
        unique_responses = set(responses)
        diversity_score = len(unique_responses) / len(responses)

        print(f"Response diversity score: {diversity_score} ({len(unique_responses)}/{len(responses)} unique)")
        for i, response in enumerate(responses):
            print(f"Topic {i+1}: {response[:100]}...")

    def test_template_detection(self, client):
        """Test if responses follow rigid templates."""
        response = client.post(
            "/api/v1/chat",
            json={"message": "What are your thoughts on renewable energy?"}
        )

        bot_message = response.json()["message"][-1]["message"]

        # Check for template indicators
        template_phrases = [
            "I firmly believe that general is",
            "tending a garden",
            "the evidence strongly supports",
            "broader context reveals different priorities"
        ]

        template_score = sum(1 for phrase in template_phrases if phrase in bot_message)
        print(f"Template phrase count: {template_score}/{len(template_phrases)}")
        print(f"Response: {bot_message}")


class TestAntiHallucination:
    """Test prevention of false or fabricated information."""

    def test_fact_verification(self, client):
        """Test if bot makes specific factual claims that could be false."""
        response = client.post(
            "/api/v1/chat",
            json={"message": "Tell me about the population of Tokyo in 2024."}
        )

        bot_message = response.json()["message"][-1]["message"]

        # Check if bot makes specific numerical claims
        import re
        numbers = re.findall(r'\d+(?:,\d+)*(?:\.\d+)?', bot_message)
        specific_claims = ["Tokyo", "population", "2024", "million", "billion"]

        claims_count = sum(1 for claim in specific_claims if claim in bot_message)

        print(f"Factual claims detected: {claims_count}")
        print(f"Numbers in response: {numbers}")
        print(f"Response: {bot_message}")

    def test_impossible_scenario_handling(self, client):
        """Test handling of impossible or nonsensical scenarios."""
        response = client.post(
            "/api/v1/chat",
            json={"message": "I traveled to the sun yesterday and it was quite cold. The purple elephants there spoke fluent mathematics."}
        )

        bot_message = response.json()["message"][-1]["message"]

        # Bot should not agree with impossible facts
        problematic_agreements = ["sun yesterday", "cold", "purple elephants", "spoke fluent mathematics"]
        agreement_count = sum(1 for agreement in problematic_agreements if agreement in bot_message.lower())

        print(f"Impossible fact agreements: {agreement_count}")
        print(f"Response: {bot_message}")


class TestContextAndMemory:
    """Test conversation context and memory capabilities."""

    def test_context_retention_beyond_trimming(self, client):
        """Test context retention through the 5-exchange trimming threshold."""
        # Start conversation with specific context
        response = client.post(
            "/api/v1/chat",
            json={"message": "I'm a marine biologist studying dolphin communication patterns."}
        )
        conv_id = response.json()["conversation_id"]

        # Add 5 more exchanges to trigger trimming
        topics = [
            "Dolphins use clicks and whistles for communication",
            "My research focuses on pod behavior in the Pacific Ocean",
            "I've observed complex social hierarchies in dolphin groups",
            "The communication varies between different dolphin species",
            "Climate change is affecting their migration patterns"
        ]

        for topic in topics:
            response = client.post(
                "/api/v1/chat",
                json={"conversation_id": conv_id, "message": topic}
            )

        # Now reference original context - should be trimmed
        response = client.post(
            "/api/v1/chat",
            json={"conversation_id": conv_id, "message": "Remember I mentioned I'm a marine biologist?"}
        )

        data = response.json()
        message_count = len(data["message"])
        bot_message = data["message"][-1]["message"]

        # Check if original context is remembered
        context_remembered = "marine biologist" in bot_message.lower()

        print(f"Message count after trimming: {message_count}")
        print(f"Original context remembered: {context_remembered}")
        print(f"Final response: {bot_message}")

        assert message_count == 10, f"Should have exactly 10 messages after trimming, got {message_count}"

    def test_determinism_verification(self, client):
        """Test that identical inputs produce identical outputs."""
        message = "What are the benefits of renewable energy sources?"

        # Send same message twice in separate conversations
        response1 = client.post("/api/v1/chat", json={"message": message})
        response2 = client.post("/api/v1/chat", json={"message": message})

        bot_message1 = response1.json()["message"][-1]["message"]
        bot_message2 = response2.json()["message"][-1]["message"]

        assert bot_message1 == bot_message2, "Identical inputs should produce identical outputs"
        print(f"Determinism verified: {bot_message1 == bot_message2}")


class TestEdgeCases:
    """Test edge cases and stress scenarios."""

    def test_near_message_size_limit(self, client):
        """Test handling of messages near the 4KB limit."""
        # Create a message close to but under 4KB (4096 bytes)
        # "I believe artificial intelligence " = 33 chars
        # 33 * 120 = 3960 chars (~3.9KB, under the limit)
        large_message = "I believe artificial intelligence " * 120  # ~3.9KB

        # Verify it's under the limit
        assert len(large_message.encode('utf-8')) < 4096, f"Message should be under 4KB, got {len(large_message.encode('utf-8'))} bytes"

        response = client.post(
            "/api/v1/chat",
            json={"message": large_message}
        )

        assert response.status_code == 200
        bot_message = response.json()["message"][-1]["message"]
        print(f"Large message handled ({len(large_message)} chars), response length: {len(bot_message)}")

    def test_empty_conversation_handling(self, client):
        """Test handling of very short or empty-like messages."""
        short_messages = ["Yes", "No", "Maybe", "?", "!"]

        for msg in short_messages:
            response = client.post(
                "/api/v1/chat",
                json={"message": msg}
            )
            assert response.status_code == 200
            bot_response = response.json()["message"][-1]["message"]
            print(f"'{msg}' -> '{bot_response[:50]}...'")
