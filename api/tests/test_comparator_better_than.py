"""Test generic comparator engine for 'A is better than B' patterns."""
import pytest

from ..handlers import DebateEngine
from ..models import Turn


class TestComparatorBetterThan:
    """Test comparator handling for 'better than' patterns."""

    def test_coke_vs_pepsi_better_than(self):
        """Test 'explain why coke is better than pepsi' response."""
        engine = DebateEngine()

        # Test detection
        comparator_match = engine.detect_comparator("explain why coke is better than pepsi", "en")
        assert comparator_match is not None, "Should detect comparator pattern"
        assert comparator_match["a"] == "coke"
        assert comparator_match["b"] == "pepsi"
        assert comparator_match["preference"] == "a"

        # Test response generation
        conversation_history = []
        response = engine.generate_response(
            "general",
            "opposing",
            "explain why coke is better than pepsi",
            conversation_history,
            "en",
        )

        response_lower = response.lower()

        # Should mention both items
        assert "coke" in response_lower, f"Response should mention Coke: {response}"
        assert "pepsi" in response_lower, f"Response should mention Pepsi: {response}"

        # Should take opposite side (argue for Pepsi when user prefers Coke)
        # Should contain axis-based arguments (generic or food domain)
        generic_axis_terms = [
            "more direct",
            "requires additional context",
            "easier to get started",
            "demands initial practice",
            "prioritizes the essential",
            "coherent long-term decisions",
            "reduces friction",
            "adds extra steps",
        ]
        food_axis_terms = [
            "base flavor",
            "sweetness",
            "carbonation",
            "aromatically",
            "aftertaste",
            "pairing",
            "over repeated sips",
            "stays steadier",
        ]
        axis_found = any(term in response_lower for term in (generic_axis_terms + food_axis_terms))
        assert axis_found, f"Should contain axis-based arguments: {response}"

        # Should NOT mention unrelated topics
        unrelated_topics = ["technology", "climate", "education", "environment"]
        unrelated_found = any(topic in response_lower for topic in unrelated_topics)
        assert not unrelated_found, f"Should not mention unrelated topics: {response}"

    def test_spanish_mejor_que_pattern(self):
        """Test Spanish 'mejor que' pattern."""
        engine = DebateEngine()

        # Test Spanish detection and response
        conversation_history = []
        response = engine.generate_response(
            "general", "opposing", "coca cola es mejor que pepsi", conversation_history, "es"
        )

        response_lower = response.lower()

        # Should mention both items in Spanish context
        assert any(
            term in response_lower for term in ["coca", "cola", "pepsi"]
        ), f"Should mention brands: {response}"

        # Should contain Spanish axis arguments (generic or food domain)
        spanish_generic_axis_terms = [
            "decisiones coherentes",
            "soluciones ad hoc",
            "más fácil empezar",
            "se adapta mejor",
            "reduce fricción",
        ]
        spanish_food_axis_terms = [
            "sabor base",
            "dulzor",
            "carbonatación",
            "aroma",
            "postgusto",
            "versatilidad",
        ]
        spanish_axis_found = any(
            term in response_lower
            for term in (spanish_generic_axis_terms + spanish_food_axis_terms)
        )
        assert spanish_axis_found, f"Should contain Spanish axis arguments: {response}"

    def test_deterministic_responses(self):
        """Test that comparator responses are deterministic."""
        engine = DebateEngine()
        conversation_history = []

        response1 = engine.generate_response(
            "general", "opposing", "iPhone is better than Android", conversation_history, "en"
        )

        response2 = engine.generate_response(
            "general", "opposing", "iPhone is better than Android", conversation_history, "en"
        )

        assert response1 == response2, "Responses should be deterministic for same input"

    def test_stance_opposite_logic(self):
        """Test that bot takes opposite stance consistently."""
        engine = DebateEngine()

        test_cases = [
            ("red is better than blue", "red", "blue"),  # User prefers red, bot argues for blue
            ("vim is superior to emacs", "vim", "emacs"),  # User prefers vim, bot argues for emacs
        ]

        for user_message, user_pref, bot_pref in test_cases:
            conversation_history = []
            response = engine.generate_response(
                "general", "opposing", user_message, conversation_history, "en"
            )

            response_lower = response.lower()

            # Response should argue for the opposite side
            # Check that bot side is mentioned positively in axis arguments
            assert (
                bot_pref.lower() in response_lower
            ), f"Should mention bot's side {bot_pref}: {response}"
            assert (
                user_pref.lower() in response_lower
            ), f"Should mention user's side {user_pref}: {response}"

    def test_no_unrelated_topic_drift(self):
        """Test that responses focus on comparison and don't drift to unrelated topics."""
        engine = DebateEngine()

        test_cases = [
            "Python is better than Java",
            "cats are better than dogs",
            "winter is better than summer",
        ]

        for user_message in test_cases:
            conversation_history = []
            response = engine.generate_response(
                "general", "opposing", user_message, conversation_history, "en"
            )

            response_lower = response.lower()

            # Should not drift into unrelated domains
            forbidden_terms = [
                "technology",
                "climate",
                "environment",
                "carbon",
                "emissions",
                "renewable",
                "education",
                "school",
                "spirituality",
                "meditation",
            ]

            forbidden_found = [term for term in forbidden_terms if term in response_lower]
            assert (
                not forbidden_found
            ), f"Should not mention unrelated topics {forbidden_found}: {response}"

            # Should contain generic axis terminology (from any of the possible axes)
            axis_terms = [
                "immediate results",
                "reduces friction",
                "adds extra steps",
                "more intuitive",
                "steep curve",
                "easier to get started",
                "demands initial investment",
                "coherent long-term decisions",
                "ad hoc solutions",
                "prioritizes the essential",
                "scatters attention",
                "adapts better to changes",
                "structural rigidity",
                "more direct",
                "requires additional context",
                "minimizes interruptions",
                "introduce micro-decisions",
            ]
            axis_found = any(term in response_lower for term in axis_terms)
            assert axis_found, f"Should focus on axis-based comparisons: {response}"

    def test_claim_mapping_better_than(self):
        """Test specific claim mapping for 'better than' patterns."""
        engine = DebateEngine()
        conversation_history = []

        response = engine.generate_response(
            "general", "opposing", "Mac is better than PC", conversation_history, "en"
        )

        response_lower = response.lower()

        # Should include the specific claim mapping format
        claim_patterns = [
            "your core claim is that mac beats pc",
            "i maintain the opposite for the reasons above",
        ]

        claim_found = any(pattern in response_lower for pattern in claim_patterns)
        assert claim_found, f"Should include claim mapping for 'better than': {response}"

    def test_structure_preservation(self):
        """Test that responses maintain expected structure (opening + axes + claim + closing)."""
        engine = DebateEngine()
        conversation_history = []

        response = engine.generate_response(
            "general", "opposing", "chess is better than checkers", conversation_history, "en"
        )

        response_lower = response.lower()

        # Should have opening
        openings = ["i can accept", "it's worth considering", "if we test what happens"]
        opening_found = any(opening in response_lower for opening in openings)
        assert opening_found, f"Should have opening: {response}"

        # Should have closing
        closings = ["shouldn't be dismissed", "this difference shows", "turns out more sensible"]
        closing_found = any(closing in response_lower for closing in closings)
        assert closing_found, f"Should have closing: {response}"

        # Should have claim refutation
        claim_found = (
            "your core claim" in response_lower or "maintain the opposite" in response_lower
        )
        assert claim_found, f"Should have claim refutation: {response}"
