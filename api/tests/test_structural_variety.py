"""Test structural variety to ensure different openings/closings across turns."""
import pytest

from ..handlers import DebateEngine
from ..models import Turn


class TestStructuralVariety:
    """Test structural variety across consecutive responses."""

    def test_different_openings_closings_across_turns(self):
        """Test that 3 consecutive turns have different openings/closings."""
        engine = DebateEngine()

        # Test both languages
        for lang in ["en", "es"]:
            # Generate 3 consecutive responses with same topic/stance but different messages
            responses = []
            conversation_history = []

            for i in range(3):
                if lang == "es":
                    user_message = f"Creo que la espiritualidad es inútil {i}"
                else:
                    user_message = f"I think spirituality is useless {i}"

                # Add user turn to history
                user_turn = Turn(
                    role="user", message=user_message, sequence=len(conversation_history) + 1
                )
                conversation_history.append(user_turn)

                # Generate bot response (falling back to unconventional topic response)
                response = engine._generate_unconventional_topic_response(
                    "opposing", user_message, conversation_history, lang
                )
                responses.append(response)

                # Add bot turn to history
                bot_turn = Turn(
                    role="bot", message=response, sequence=len(conversation_history) + 1
                )
                conversation_history.append(bot_turn)

            # Extract opening phrases (first part before first period/comma)
            openings = []
            closings = []

            for response in responses:
                # Opening is typically the first sentence or clause
                parts = response.split(".", 1)
                if len(parts) > 1:
                    opening = parts[0].strip()
                    # Closing is typically the last sentence
                    sentences = response.split(".")
                    if len(sentences) > 1:
                        closing = (
                            sentences[-2].strip()
                            if sentences[-1].strip() == ""
                            else sentences[-1].strip()
                        )
                    else:
                        closing = sentences[0].strip()
                else:
                    opening = response.strip()
                    closing = response.strip()

                openings.append(opening)
                closings.append(closing)

            # Verify that not all openings are identical
            unique_openings = set(openings)
            assert len(unique_openings) > 1, f"All openings are identical in {lang}: {openings}"

            # Verify that not all closings are identical
            unique_closings = set(closings)
            assert len(unique_closings) > 1, f"All closings are identical in {lang}: {closings}"

    def test_structural_elements_rotation(self):
        """Test that structural elements rotate to avoid immediate repetition."""
        engine = DebateEngine()

        # Test with English
        lang = "en"
        conversation_history = []

        # Generate first response
        user_message1 = "This is subjective"
        user_turn1 = Turn(role="user", message=user_message1, sequence=1)
        conversation_history.append(user_turn1)

        response1 = engine._generate_unconventional_topic_response(
            "opposing", user_message1, conversation_history, lang
        )
        bot_turn1 = Turn(role="bot", message=response1, sequence=2)
        conversation_history.append(bot_turn1)

        # Generate second response with same seed base
        user_message2 = "This is subjective"  # Same message to test rotation
        user_turn2 = Turn(role="user", message=user_message2, sequence=3)
        conversation_history.append(user_turn2)

        response2 = engine._generate_unconventional_topic_response(
            "opposing", user_message2, conversation_history, lang
        )

        # The responses should be different due to rotation logic
        assert response1 != response2, "Responses should differ due to rotation to avoid repetition"

        # Verify rotation works by checking structural elements don't repeat
        structural_banks = engine.structural_banks[lang]

        # At least one structural element should have rotated
        different_elements = False
        for element_type in ["openings", "bodies", "closings"]:
            elements = structural_banks[element_type]
            for element in elements:
                if element in response1 and element not in response2:
                    different_elements = True
                    break
                if element not in response1 and element in response2:
                    different_elements = True
                    break

        assert different_elements, "No structural elements rotated between responses"

    def test_deterministic_structural_selection(self):
        """Test that structural selection is deterministic for same inputs."""
        engine = DebateEngine()

        for lang in ["en", "es"]:
            conversation_history = []
            user_message = "This is completely subjective"

            # Generate same response twice
            response1 = engine._generate_unconventional_topic_response(
                "opposing", user_message, conversation_history, lang
            )

            response2 = engine._generate_unconventional_topic_response(
                "opposing", user_message, conversation_history, lang
            )

            # Should be identical for same inputs
            assert response1 == response2, f"Responses not deterministic for {lang}"
