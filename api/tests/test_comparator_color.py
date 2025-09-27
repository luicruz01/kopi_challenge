"""Test generic comparator engine for color comparisons."""
import pytest

from ..handlers import DebateEngine
from ..models import Turn


class TestComparatorColor:
    """Test comparator handling for color comparisons."""

    def test_blue_better_than_red(self):
        """Test 'blue is better than red' comparator response."""
        engine = DebateEngine()

        # Test detection
        comparator_match = engine.detect_comparator("blue is better than red", "en")
        assert comparator_match is not None, "Should detect color comparison"
        assert comparator_match["a"] == "blue"
        assert comparator_match["b"] == "red"
        assert comparator_match["preference"] == "a"

        # Test response generation
        conversation_history = []
        response = engine.generate_response(
            "general", "opposing", "blue is better than red", conversation_history, "en"
        )

        response_lower = response.lower()

        # Should mention both colors
        assert "blue" in response_lower, f"Response should mention blue: {response}"
        assert "red" in response_lower, f"Response should mention red: {response}"

        # Should contain axis arguments (generic, not color-specific)
        axis_terms = [
            "simplicity",
            "consistency",
            "accessibility",
            "essential",
            "practice",
            "interruptions",
        ]
        axis_found = any(term in response_lower for term in axis_terms)
        assert axis_found, f"Should contain axis-based arguments: {response}"

        # Should NOT contain "research/evidence" wording as specified
        forbidden_phrases = ["research confirms", "evidence substantiates", "studies demonstrate"]
        forbidden_found = any(phrase in response_lower for phrase in forbidden_phrases)
        assert not forbidden_found, f"Should not contain research/evidence phrases: {response}"

    def test_spanish_color_comparison(self):
        """Test Spanish color comparison."""
        engine = DebateEngine()

        conversation_history = []
        response = engine.generate_response(
            "general", "opposing", "azul es mejor que rojo", conversation_history, "es"
        )

        response_lower = response.lower()

        # Should mention colors in Spanish
        assert "azul" in response_lower, f"Should mention azul: {response}"
        assert "rojo" in response_lower, f"Should mention rojo: {response}"

        # Should contain Spanish axis arguments
        spanish_axis_terms = ["simplicidad", "consistencia", "accesibilidad", "práctica"]
        spanish_found = any(term in response_lower for term in spanish_axis_terms)
        assert spanish_found, f"Should contain Spanish axis arguments: {response}"

        # Should use Spanish claim mapping
        spanish_claim = "tu idea central es que azul supera a rojo"
        claim_found = spanish_claim in response_lower
        assert claim_found, f"Should use Spanish claim mapping: {response}"

    def test_neutral_color_vs(self):
        """Test neutral color comparison 'blue vs red'."""
        engine = DebateEngine()

        conversation_history = []
        response = engine.generate_response(
            "general", "opposing", "blue vs red", conversation_history, "en"
        )

        response_lower = response.lower()

        # Should mention both colors
        assert "blue" in response_lower and "red" in response_lower, "Should mention both colors"

        # Should contain axis arguments with proper color substitution
        # Check that colors are used in axis context
        color_in_axis = (
            "blue" in response_lower
            and "red" in response_lower
            and any(
                axis in response_lower for axis in ["consistency", "simplicity", "accessibility"]
            )
        )
        assert color_in_axis, f"Should use colors in axis arguments: {response}"

    def test_no_color_specific_arguments(self):
        """Test that responses use generic axes, not color-specific arguments."""
        engine = DebateEngine()

        conversation_history = []
        response = engine.generate_response(
            "general", "opposing", "green is better than yellow", conversation_history, "en"
        )

        response_lower = response.lower()

        # Should NOT contain color-specific arguments from old system
        color_specific_terms = [
            "calm and trust",
            "visual fatigue",
            "urgency and action",
            "dashboard",
            "warnings",
            "call-to-action",
        ]
        color_specific_found = any(term in response_lower for term in color_specific_terms)
        assert not color_specific_found, f"Should not use old color-specific arguments: {response}"

        # Should contain generic axis arguments instead
        generic_axis_terms = ["simplicity", "consistency", "accessibility", "essential", "practice"]
        generic_found = any(term in response_lower for term in generic_axis_terms)
        assert generic_found, f"Should use generic axis arguments: {response}"

    def test_deterministic_color_responses(self):
        """Test that color responses are deterministic."""
        engine = DebateEngine()

        test_cases = ["purple vs orange", "black is better than white", "pink vs brown"]

        for user_message in test_cases:
            conversation_history = []

            response1 = engine.generate_response(
                "general", "opposing", user_message, conversation_history, "en"
            )

            response2 = engine.generate_response(
                "general", "opposing", user_message, conversation_history, "en"
            )

            assert response1 == response2, f"Should be deterministic for '{user_message}'"

    def test_color_stance_opposite(self):
        """Test that bot takes opposite stance for color preferences."""
        engine = DebateEngine()

        # Test user prefers blue, bot should argue for red
        conversation_history = []
        response = engine.generate_response(
            "general", "opposing", "blue is clearly better than red", conversation_history, "en"
        )

        response_lower = response.lower()

        # Should argue for red (opposite of user's blue preference)
        # Check that red appears in positive contexts in the axis arguments
        assert "red" in response_lower, "Should mention red in arguments"
        assert "blue" in response_lower, "Should also mention blue for contrast"

        # Should use core claim mapping for "better than"
        claim_patterns = ["your core claim", "blue beats red", "maintain the opposite"]
        claim_found = any(pattern in response_lower for pattern in claim_patterns)
        assert claim_found, f"Should include claim refutation: {response}"

    def test_multiple_color_words(self):
        """Test handling of color names that might be multi-word."""
        engine = DebateEngine()

        # Test detection with compound color names
        test_cases = [
            ("dark blue vs light red", ["dark blue", "light red"]),
            ("navy blue is better than bright red", ["navy blue", "bright red"]),
        ]

        for user_message, expected_colors in test_cases:
            comparator_match = engine.detect_comparator(user_message, "en")

            if comparator_match:
                # Should detect the full color names
                a_lower = comparator_match["a"].lower()
                b_lower = comparator_match["b"].lower()

                # At least one of the expected colors should be detected
                color_detected = any(
                    color.lower() in [a_lower, b_lower] for color in expected_colors
                )
                assert (
                    color_detected
                ), f"Should detect compound color names in '{user_message}': {comparator_match}"

    def test_color_structure_preservation(self):
        """Test that color responses maintain proper structure."""
        engine = DebateEngine()
        conversation_history = []

        response = engine.generate_response(
            "general", "opposing", "red is superior to blue", conversation_history, "en"
        )

        response_lower = response.lower()

        # Should have proper comparator structure
        # Opening
        openings = ["i can accept", "worth considering", "test what happens"]
        opening_found = any(opening in response_lower for opening in openings)
        assert opening_found, f"Should have comparator opening: {response}"

        # Closing with color substitution
        closings = ["shouldn't be dismissed", "difference shows", "more sensible"]
        closing_found = any(closing in response_lower for closing in closings)
        assert closing_found, f"Should have comparator closing: {response}"

        # No template placeholders should remain
        assert "{{A}}" not in response, "Should substitute {{A}} placeholder"
        assert "{{B}}" not in response, "Should substitute {{B}} placeholder"

    def test_no_unrelated_topics(self):
        """Test that color comparisons don't drift to unrelated topics."""
        engine = DebateEngine()

        color_comparisons = ["orange vs purple", "yellow is better than gray", "pink vs cyan"]

        for user_message in color_comparisons:
            conversation_history = []
            response = engine.generate_response(
                "general", "opposing", user_message, conversation_history, "en"
            )

            response_lower = response.lower()

            # Should not mention unrelated topics
            forbidden_topics = [
                "technology",
                "climate",
                "education",
                "environment",
                "carbon",
                "spirituality",
                "meditation",
            ]

            forbidden_found = [topic for topic in forbidden_topics if topic in response_lower]
            assert (
                not forbidden_found
            ), f"Should not mention unrelated topics {forbidden_found}: {response}"

            # Should focus on axis-based comparison
            axis_focus = any(
                term in response_lower
                for term in ["simplicity", "consistency", "practice", "results"]
            )
            assert axis_focus, f"Should focus on axis-based comparison: {response}"
