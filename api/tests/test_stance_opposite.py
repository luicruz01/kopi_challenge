"""Tests for opposite stance logic."""
import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestOppositeStance:
    """Test that bot always takes opposite stance of user."""

    def test_pro_technology_gets_contra_response(self, client):
        """Test clearly pro-technology message gets contra bot stance."""
        # Strong pro-technology message
        response = client.post(
            "/api/v1/chat",
            json={"message": "Technology is amazing and will improve our lives significantly"}
        )

        assert response.status_code == 200
        data = response.json()
        bot_message = data["message"][-1]["message"].lower()

        # Bot should take opposing stance - look for contra indicators
        contra_indicators = [
            "serious issues", "careful consideration", "concerns that cannot be ignored",
            "challenges that outweigh", "problems", "risks", "dangers"
        ]

        pro_indicators = [
            "beneficial and necessary", "crucial advancement", "indispensable benefits",
            "fundamentally beneficial", "represents progress"
        ]

        contra_found = any(indicator in bot_message for indicator in contra_indicators)
        pro_found = any(indicator in bot_message for indicator in pro_indicators)

        # Should be contra (opposing user's pro stance)
        assert contra_found or not pro_found, f"Expected contra stance but got: {bot_message}"

    def test_contra_technology_gets_pro_response(self, client):
        """Test clearly contra-technology message gets pro bot stance."""
        # Strong contra-technology message
        response = client.post(
            "/api/v1/chat",
            json={"message": "Technology is dangerous and harmful to society, we should limit it"}
        )

        assert response.status_code == 200
        data = response.json()
        bot_message = data["message"][-1]["message"].lower()

        # Bot should take supporting stance - look for pro indicators
        pro_indicators = [
            "beneficial and necessary", "crucial advancement", "indispensable benefits",
            "fundamentally beneficial", "represents progress"
        ]

        pro_found = any(indicator in bot_message for indicator in pro_indicators)
        assert pro_found, f"Expected pro stance but got: {bot_message}"

    def test_stance_consistency_throughout_conversation(self, client):
        """Test bot maintains opposite stance throughout entire conversation."""
        # Start with pro-climate message
        response1 = client.post(
            "/api/v1/chat",
            json={"message": "Climate action is essential and renewable energy is the future"}
        )

        assert response1.status_code == 200
        conv_id = response1.json()["conversation_id"]
        bot_message1 = response1.json()["message"][-1]["message"].lower()

        # Should be contra climate initially
        initial_contra = any(phrase in bot_message1 for phrase in ["serious issues", "concerns", "challenges"])
        initial_pro = any(phrase in bot_message1 for phrase in ["beneficial", "advancement", "benefits"])

        # Continue conversation - bot should maintain same stance
        response2 = client.post(
            "/api/v1/chat",
            json={"conversation_id": conv_id, "message": "Solar and wind power are clean and sustainable"}
        )

        response3 = client.post(
            "/api/v1/chat",
            json={"conversation_id": conv_id, "message": "We must transition away from fossil fuels"}
        )

        bot_message2 = response2.json()["message"][-1]["message"].lower()
        bot_message3 = response3.json()["message"][-1]["message"].lower()

        # Check stance consistency
        msg2_contra = any(phrase in bot_message2 for phrase in ["serious issues", "concerns", "challenges"])
        msg2_pro = any(phrase in bot_message2 for phrase in ["beneficial", "advancement", "benefits"])

        msg3_contra = any(phrase in bot_message3 for phrase in ["serious issues", "concerns", "challenges"])
        msg3_pro = any(phrase in bot_message3 for phrase in ["beneficial", "advancement", "benefits"])

        # Stance should be consistent across all messages
        if initial_contra and not initial_pro:
            # Started contra, should stay contra
            assert msg2_contra or not msg2_pro, f"Stance flip in message 2: {bot_message2}"
            assert msg3_contra or not msg3_pro, f"Stance flip in message 3: {bot_message3}"
        elif initial_pro and not initial_contra:
            # Started pro, should stay pro
            assert msg2_pro or not msg2_contra, f"Stance flip in message 2: {bot_message2}"
            assert msg3_pro or not msg3_contra, f"Stance flip in message 3: {bot_message3}"

    def test_spanish_opposite_stance(self, client):
        """Test opposite stance logic works in Spanish."""
        # Pro-technology message in Spanish
        response = client.post(
            "/api/v1/chat",
            json={"message": "La tecnología es excelente y beneficiosa para la humanidad"}
        )

        assert response.status_code == 200
        bot_message = response.json()["message"][-1]["message"]

        # Should be in Spanish and take opposing stance
        spanish_indicators = ["que", "es", "la", "el", "de"]
        spanish_found = sum(1 for word in spanish_indicators if word in bot_message.lower())
        assert spanish_found >= 3, f"Should respond in Spanish: {bot_message}"

        # Should express opposing stance
        contra_spanish = ["problemas serios", "preocupaciones", "desafíos", "riesgos"]
        contra_found = any(phrase in bot_message.lower() for phrase in contra_spanish)

        # Or at least not strongly pro
        pro_spanish = ["beneficioso y necesario", "fundamental", "indispensable"]
        pro_found = any(phrase in bot_message.lower() for phrase in pro_spanish)

        assert contra_found or not pro_found, f"Expected Spanish contra stance: {bot_message}"

    def test_negation_detection(self, client):
        """Test stance detection with negation markers."""
        # Message with negations should be detected as contra
        response = client.post(
            "/api/v1/chat",
            json={"message": "I don't think technology is not beneficial, it has no real advantages"}
        )

        assert response.status_code == 200
        bot_message = response.json()["message"][-1]["message"].lower()

        # User was contra (due to negations), so bot should be pro
        pro_indicators = ["beneficial", "advancement", "benefits", "progress"]
        pro_found = any(indicator in bot_message for indicator in pro_indicators)
        assert pro_found, f"Expected pro stance against user's negated contra position: {bot_message}"
