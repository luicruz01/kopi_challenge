"""Tests for unconventional topic fallback handling."""
import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestUnconventionalTopicFallback:
    """Test graceful fallback for unconventional/subjective topics."""

    def test_pineapple_pizza_fallback(self, client):
        """Test pineapple pizza topic uses fallback response."""
        response = client.post(
            "/api/v1/chat", json={"message": "Pineapple belongs on pizza and makes it delicious"}
        )

        assert response.status_code == 200
        bot_message = response.json()["message"][-1]["message"]

        # Should acknowledge subjectivity
        subjectivity_indicators = [
            "subjective matter",
            "personal preference",
            "matter of preference",
            "recognize this",
            "acknowledge",
        ]
        subjectivity_found = any(
            indicator in bot_message.lower() for indicator in subjectivity_indicators
        )
        assert subjectivity_found, f"Should acknowledge subjectivity: {bot_message}"

        # Should not contain tech/climate specific arguments
        specific_tech_args = [
            "innovation advancement",
            "efficiency improvements",
            "carbon footprint",
        ]
        tech_found = any(arg in bot_message.lower() for arg in specific_tech_args)
        assert not tech_found, f"Should not contain tech-specific arguments: {bot_message}"

        # Should use generic but relevant arguments (check for argument patterns)
        generic_patterns = [
            "traditions",
            "standards",
            "consistency",
            "principles",
            "diversity",
            "preferences",
            "innovations",
            "changes",
            "improvements",
            "established",
            "approaches",
            "growth",
        ]
        generic_found = any(pattern in bot_message.lower() for pattern in generic_patterns)
        assert generic_found, f"Should contain generic argument patterns: {bot_message}"

    def test_unconventional_food_topic_spanish(self, client):
        """Test unconventional food topic fallback in Spanish."""
        response = client.post(
            "/api/v1/chat",
            json={
                "message": "Los tacos con ketchup son deliciosos y una gran innovación culinaria"
            },
        )

        assert response.status_code == 200
        bot_message = response.json()["message"][-1]["message"]

        # Should be in Spanish
        spanish_indicators = ["que", "es", "la", "el", "de", "se"]
        spanish_found = sum(1 for word in spanish_indicators if word in bot_message.lower())
        assert spanish_found >= 3, f"Should respond in Spanish: {bot_message}"

        # Should acknowledge subjectivity in Spanish
        spanish_subjectivity = ["subjetivo", "preferencias personales", "reconozco"]
        subjectivity_found = any(
            indicator in bot_message.lower() for indicator in spanish_subjectivity
        )
        assert subjectivity_found, f"Should acknowledge subjectivity in Spanish: {bot_message}"

    def test_unconventional_maintains_stance(self, client):
        """Test unconventional topic maintains consistent stance."""
        # Start with pro-unconventional stance
        response1 = client.post(
            "/api/v1/chat",
            json={"message": "Wearing socks with sandals is fashionable and practical"},
        )

        conv_id = response1.json()["conversation_id"]
        bot_message1 = response1.json()["message"][-1]["message"].lower()

        # Continue conversation
        response2 = client.post(
            "/api/v1/chat",
            json={
                "conversation_id": conv_id,
                "message": "It provides comfort and style flexibility",
            },
        )

        response3 = client.post(
            "/api/v1/chat",
            json={"conversation_id": conv_id, "message": "Many people are adopting this trend"},
        )

        bot_message2 = response2.json()["message"][-1]["message"].lower()
        bot_message3 = response3.json()["message"][-1]["message"].lower()

        # All should acknowledge subjectivity or use structural variety that handles unconventional topics
        for msg in [bot_message1, bot_message2, bot_message3]:
            subjectivity_acknowledgment = any(
                phrase in msg
                for phrase in [
                    "subjective",
                    "preference",
                    "personal",
                    "opinion",
                    "understand you might see",
                    "can accept that many",
                    "may seem like",
                    "view this as",
                ]
            )
            assert (
                subjectivity_acknowledgment
            ), f"Should acknowledge subjectivity or use appropriate opening: {msg}"

        # Check for stance consistency (all should have similar opposing or supporting tone)
        stance_indicators = {
            "opposing": ["however", "maintain that", "established", "standards", "consistency"],
            "supporting": ["support that", "diversity", "openness", "individual preferences"],
        }

        # Determine initial stance
        initial_opposing = any(phrase in bot_message1 for phrase in stance_indicators["opposing"])
        initial_supporting = any(
            phrase in bot_message1 for phrase in stance_indicators["supporting"]
        )

        if initial_opposing:
            # Should maintain opposing stance
            assert any(
                phrase in bot_message2 for phrase in stance_indicators["opposing"]
            ), f"Stance inconsistency in msg2: {bot_message2}"
            assert any(
                phrase in bot_message3 for phrase in stance_indicators["opposing"]
            ), f"Stance inconsistency in msg3: {bot_message3}"
        elif initial_supporting:
            # Should maintain supporting stance
            assert any(
                phrase in bot_message2 for phrase in stance_indicators["supporting"]
            ), f"Stance inconsistency in msg2: {bot_message2}"
            assert any(
                phrase in bot_message3 for phrase in stance_indicators["supporting"]
            ), f"Stance inconsistency in msg3: {bot_message3}"

    def test_no_fabricated_facts(self, client):
        """Test that unconventional topic responses don't invent facts."""
        response = client.post(
            "/api/v1/chat",
            json={"message": "Purple hair is the most professional look for business meetings"},
        )

        bot_message = response.json()["message"][-1]["message"]

        # Should not contain specific statistics, studies, or factual claims
        fabricated_indicators = [
            "studies show",
            "research indicates",
            "statistics prove",
            "data confirms",
            "experts agree",
            "scientists found",
            "survey results",
            "proven fact",
            "research demonstrates",
            "analysis shows",
        ]

        fabricated_found = any(phrase in bot_message.lower() for phrase in fabricated_indicators)
        assert not fabricated_found, f"Should not fabricate facts: {bot_message}"

        # Should stick to general principles and preferences
        acceptable_phrases = [
            "generally speaking",
            "in terms of",
            "preferences",
            "principles",
            "considerations",
            "perspective",
            "approach",
            "matter of",
        ]

        acceptable_found = any(phrase in bot_message.lower() for phrase in acceptable_phrases)
        assert acceptable_found, f"Should use general principles: {bot_message}"

    def test_unconventional_movie_topic(self, client):
        """Test another unconventional topic - movie preferences."""
        response = client.post(
            "/api/v1/chat",
            json={"message": "Movies should always be watched in reverse chronological order"},
        )

        assert response.status_code == 200
        bot_message = response.json()["message"][-1]["message"]

        # Should recognize as subjective
        subjectivity_found = any(
            phrase in bot_message.lower()
            for phrase in [
                "subjective",
                "personal preference",
                "matter of preference",
                "recognize this",
            ]
        )
        assert subjectivity_found, f"Should acknowledge subjectivity: {bot_message}"

        # Should not contain movie industry facts or statistics
        movie_facts = [
            "box office",
            "industry standard",
            "director",
            "cinematography",
            "studies show",
        ]
        facts_found = any(fact in bot_message.lower() for fact in movie_facts)
        assert not facts_found, f"Should avoid specific movie facts: {bot_message}"

        # Should maintain coherent argument structure
        assert len(bot_message.split(".")) >= 3, f"Should have structured response: {bot_message}"

    def test_fallback_uses_claim_extraction(self, client):
        """Test that fallback responses properly quote user claims."""
        response = client.post(
            "/api/v1/chat",
            json={
                "message": "Eating ice cream for breakfast is the healthiest way to start the day"
            },
        )

        bot_message = response.json()["message"][-1]["message"]

        # Should quote part of user's claim
        claim_indicators = ["ice cream for breakfast", "healthiest way", "start the day"]

        claim_found = any(claim in bot_message.lower() for claim in claim_indicators)
        assert claim_found, f"Should quote user's claim: {bot_message}"

        # Should be in refutation format (either old format or new claim mapping format)
        old_refutation_format = any(
            phrase in bot_message.lower()
            for phrase in ["while you mention", "although you", "your mention of"]
        )

        new_refutation_format = any(
            phrase in bot_message.lower()
            for phrase in [
                "but this perspective overlooks",
                "your main claim is that",
                "but this overlooks",
                "yet this perspective misses",
                "though this fails to account",
            ]
        )

        assert (
            old_refutation_format or new_refutation_format
        ), f"Should use refutation format (old or new): {bot_message}"
