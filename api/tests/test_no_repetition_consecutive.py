"""Test that comparator responses avoid consecutive repetition of same elements."""
import pytest

from ..handlers import DebateEngine
from ..models import Turn


class TestNoRepetitionConsecutive:
    """Test no consecutive repetition in comparator responses."""

    def test_no_consecutive_opening_repetition(self):
        """Test that the same opening is not repeated in consecutive turns."""
        engine = DebateEngine()
        conversation_history = []

        # Generate 3 consecutive responses on the same pair
        responses = []
        for i in range(3):
            user_message = f"cats vs dogs {i}"  # Vary slightly to avoid exact caching
            user_turn = Turn(
                role="user", message=user_message, sequence=len(conversation_history) + 1
            )
            conversation_history.append(user_turn)

            response = engine.generate_response(
                "general", "opposing", user_message, conversation_history, "en"
            )
            responses.append(response)

            bot_turn = Turn(role="bot", message=response, sequence=len(conversation_history) + 1)
            conversation_history.append(bot_turn)

        # Extract openings (first phrase before comma)
        openings = []
        for response in responses:
            # Opening is typically before the first comma
            if "," in response:
                opening = response.split(",")[0].strip().lower()
                openings.append(opening)
            else:
                openings.append(response[:50].lower())  # First 50 chars as fallback

        # Check that not all openings are identical
        unique_openings = set(openings)
        assert len(unique_openings) > 1, f"Openings should vary across turns: {openings}"

        # Check that no consecutive openings are identical
        for i in range(len(openings) - 1):
            assert (
                openings[i] != openings[i + 1]
            ), f"Consecutive openings should differ: {openings[i]} vs {openings[i + 1]}"

    def test_no_consecutive_closing_repetition(self):
        """Test that the same closing is not repeated in consecutive turns."""
        engine = DebateEngine()
        conversation_history = []

        # Generate 3 consecutive responses
        responses = []
        for i in range(3):
            user_message = f"iPhone vs Android discussion {i}"
            user_turn = Turn(
                role="user", message=user_message, sequence=len(conversation_history) + 1
            )
            conversation_history.append(user_turn)

            response = engine.generate_response(
                "general", "opposing", user_message, conversation_history, "en"
            )
            responses.append(response)

            bot_turn = Turn(role="bot", message=response, sequence=len(conversation_history) + 1)
            conversation_history.append(bot_turn)

        # Extract closings (last sentence)
        closings = []
        for response in responses:
            sentences = response.split(".")
            if len(sentences) > 1:
                # Get the last non-empty sentence
                closing = (
                    sentences[-2].strip().lower()
                    if sentences[-1].strip() == ""
                    else sentences[-1].strip().lower()
                )
                closings.append(closing)
            else:
                closings.append(response[-50:].lower())  # Last 50 chars as fallback

        # Check that closings vary
        unique_closings = set(closings)
        assert len(unique_closings) > 1, f"Closings should vary across turns: {closings}"

    def test_no_consecutive_axis_repetition(self):
        """Test that the same axis is not repeated in consecutive turns."""
        engine = DebateEngine()
        conversation_history = []

        # Generate responses and track axes
        responses = []
        for i in range(3):
            user_message = f"Windows vs Mac {i}"
            user_turn = Turn(
                role="user", message=user_message, sequence=len(conversation_history) + 1
            )
            conversation_history.append(user_turn)

            response = engine.generate_response(
                "general", "opposing", user_message, conversation_history, "en"
            )
            responses.append(response)

            bot_turn = Turn(role="bot", message=response, sequence=len(conversation_history) + 1)
            conversation_history.append(bot_turn)

        # Check for axis diversity
        axis_keywords = [
            "simplicity",
            "consistency",
            "accessibility",
            "essential",
            "practice",
            "interruptions",
            "results",
        ]

        response_axes = []
        for response in responses:
            response_lower = response.lower()
            found_axes = [axis for axis in axis_keywords if axis in response_lower]
            response_axes.append(found_axes)

        # Should have some variation in axes used
        all_axes_used = set()
        for axes in response_axes:
            all_axes_used.update(axes)

        assert (
            len(all_axes_used) > 1
        ), f"Should use different axes across responses: {response_axes}"

    def test_deterministic_but_varied_responses(self):
        """Test that responses are deterministic for same input but vary for different inputs."""
        engine = DebateEngine()

        # Same exact input should give same response
        conversation_history1 = []
        response1a = engine.generate_response(
            "general", "opposing", "coffee vs tea", conversation_history1, "en"
        )

        conversation_history2 = []
        response1b = engine.generate_response(
            "general", "opposing", "coffee vs tea", conversation_history2, "en"
        )

        assert response1a == response1b, "Same input should give same response"

        # Different inputs should give different responses
        conversation_history3 = []
        response2 = engine.generate_response(
            "general",
            "opposing",
            "tea vs coffee",
            conversation_history3,
            "en",  # Reversed order
        )

        assert response1a != response2, "Different inputs should give different responses"

    def test_rotation_with_conversation_history(self):
        """Test that rotation logic works properly with conversation history."""
        engine = DebateEngine()

        # Start a conversation
        conversation_history = []

        # First turn
        user_turn1 = Turn(role="user", message="Python vs Java", sequence=1)
        conversation_history.append(user_turn1)

        response1 = engine.generate_response(
            "general", "opposing", "Python vs Java", conversation_history, "en"
        )

        bot_turn1 = Turn(role="bot", message=response1, sequence=2)
        conversation_history.append(bot_turn1)

        # Second turn - should avoid repetition from first turn
        user_turn2 = Turn(role="user", message="Python vs Java again", sequence=3)
        conversation_history.append(user_turn2)

        response2 = engine.generate_response(
            "general", "opposing", "Python vs Java again", conversation_history, "en"
        )

        bot_turn2 = Turn(role="bot", message=response2, sequence=4)
        conversation_history.append(bot_turn2)

        # Third turn - should avoid repetition from second turn
        user_turn3 = Turn(role="user", message="Python vs Java once more", sequence=5)
        conversation_history.append(user_turn3)

        response3 = engine.generate_response(
            "general", "opposing", "Python vs Java once more", conversation_history, "en"
        )

        # Check that responses are different
        assert response1 != response2, "Second response should differ from first"
        assert response2 != response3, "Third response should differ from second"

        # But they should all be valid comparator responses
        for response in [response1, response2, response3]:
            response_lower = response.lower()
            assert (
                "python" in response_lower and "java" in response_lower
            ), f"Should mention both languages: {response}"

    def test_spanish_no_consecutive_repetition(self):
        """Test no consecutive repetition in Spanish responses."""
        engine = DebateEngine()
        conversation_history = []

        # Generate Spanish responses
        responses = []
        for i in range(3):
            user_message = f"gatos vs perros {i}"
            user_turn = Turn(
                role="user", message=user_message, sequence=len(conversation_history) + 1
            )
            conversation_history.append(user_turn)

            response = engine.generate_response(
                "general", "opposing", user_message, conversation_history, "es"
            )
            responses.append(response)

            bot_turn = Turn(role="bot", message=response, sequence=len(conversation_history) + 1)
            conversation_history.append(bot_turn)

        # Check for variety in Spanish openings
        spanish_openings = ["puedo aceptar", "vale la pena", "si ponemos a prueba"]

        opening_matches = []
        for response in responses:
            response_lower = response.lower()
            matched_opening = None
            for opening in spanish_openings:
                if opening in response_lower:
                    matched_opening = opening
                    break
            opening_matches.append(matched_opening)

        # Should have some variety (not all the same opening)
        unique_openings = set(filter(None, opening_matches))
        assert (
            len(unique_openings) > 1
        ), f"Should have variety in Spanish openings: {opening_matches}"

    def test_example_no_repetition_when_triggered(self):
        """Test that examples don't repeat when triggered in consecutive turns."""
        engine = DebateEngine()
        conversation_history = []

        # Generate responses with example triggers
        responses = []
        for i in range(3):
            user_message = f"give me an example of cats vs dogs {i}"
            user_turn = Turn(
                role="user", message=user_message, sequence=len(conversation_history) + 1
            )
            conversation_history.append(user_turn)

            response = engine.generate_response(
                "general", "opposing", user_message, conversation_history, "en"
            )
            responses.append(response)

            bot_turn = Turn(role="bot", message=response, sequence=len(conversation_history) + 1)
            conversation_history.append(bot_turn)

        # All should contain examples
        for response in responses:
            response_lower = response.lower()
            example_indicators = ["for example", "concrete case", "consider how"]
            example_found = any(indicator in response_lower for indicator in example_indicators)
            assert example_found, f"Should contain example when triggered: {response}"

        # Examples should not be identical
        unique_responses = set(responses)
        assert len(unique_responses) > 1, "Responses with examples should vary"

    def test_mixed_patterns_no_repetition(self):
        """Test no repetition across different comparison patterns."""
        engine = DebateEngine()
        conversation_history = []

        # Use different patterns but same underlying comparison
        patterns = ["cats vs dogs", "cats are better than dogs", "cats versus dogs"]

        responses = []
        for pattern in patterns:
            user_turn = Turn(role="user", message=pattern, sequence=len(conversation_history) + 1)
            conversation_history.append(user_turn)

            response = engine.generate_response(
                "general", "opposing", pattern, conversation_history, "en"
            )
            responses.append(response)

            bot_turn = Turn(role="bot", message=response, sequence=len(conversation_history) + 1)
            conversation_history.append(bot_turn)

        # Should have variety even with different patterns
        unique_responses = set(responses)
        assert (
            len(unique_responses) > 1
        ), f"Should have variety across different patterns: got {len(unique_responses)} unique responses"
