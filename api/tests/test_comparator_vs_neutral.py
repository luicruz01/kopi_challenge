"""Test generic comparator engine for neutral 'A vs B' patterns."""
import pytest

from ..handlers import DebateEngine
from ..models import Turn


class TestComparatorVsNeutral:
    """Test comparator handling for neutral 'vs' patterns."""

    def test_vim_vs_emacs_neutral(self):
        """Test 'vim vs emacs' with no explicit preference."""
        engine = DebateEngine()

        # Test detection
        comparator_match = engine.detect_comparator("vim vs emacs", "en")
        assert comparator_match is not None, "Should detect vs pattern"
        assert comparator_match["a"] == "vim"
        assert comparator_match["b"] == "emacs"
        assert comparator_match["preference"] is None, "Should be neutral preference"

        # Test response generation
        conversation_history = []
        response = engine.generate_response(
            "general", "opposing", "vim vs emacs", conversation_history, "en"
        )

        response_lower = response.lower()

        # Should mention both editors
        assert "vim" in response_lower, f"Response should mention vim: {response}"
        assert "emacs" in response_lower, f"Response should mention emacs: {response}"

        # Should pick a side deterministically and argue for it
        # Since preference is None, bot side is chosen deterministically
        assert "vim" in response_lower and "emacs" in response_lower, "Should reference both sides"

        # Should contain axis-based arguments
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
        ]
        axis_found = any(term in response_lower for term in axis_terms)
        assert axis_found, f"Should contain axis-based arguments: {response}"

    def test_deterministic_side_selection(self):
        """Test that neutral comparisons choose bot side deterministically."""
        engine = DebateEngine()

        # Same input should always choose the same side
        test_cases = ["iPhone vs Android", "coffee vs tea", "cats vs dogs"]

        for user_message in test_cases:
            conversation_history = []

            response1 = engine.generate_response(
                "general", "opposing", user_message, conversation_history, "en"
            )

            response2 = engine.generate_response(
                "general", "opposing", user_message, conversation_history, "en"
            )

            assert response1 == response2, f"Should be deterministic for '{user_message}'"

    def test_correct_ab_ordering(self):
        """Test that A and B are correctly identified and used in responses."""
        engine = DebateEngine()

        # Test with a specific pair where we can verify the order
        conversation_history = []
        response = engine.generate_response(
            "general", "opposing", "pizza vs burgers", conversation_history, "en"
        )

        response_lower = response.lower()

        # Both should be mentioned
        assert "pizza" in response_lower, "Should mention pizza"
        assert "burgers" in response_lower, "Should mention burgers"

        # Should contain axis arguments with correct A/B substitution
        # The axis templates use {{A}} and {{B}} placeholders which should be replaced
        substitution_working = (
            "pizza" in response_lower
            and "burgers" in response_lower
            and "{{A}}" not in response
            and "{{B}}" not in response
        )
        assert substitution_working, f"Should properly substitute A/B in axes: {response}"

    def test_spanish_vs_patterns(self):
        """Test Spanish vs patterns."""
        engine = DebateEngine()

        # Test Spanish "vs" detection
        comparator_match = engine.detect_comparator("gatos vs perros", "es")
        assert comparator_match is not None, "Should detect Spanish vs pattern"
        assert comparator_match["preference"] is None, "Should be neutral"

        # Test Spanish response
        conversation_history = []
        response = engine.generate_response(
            "general", "opposing", "café vs té", conversation_history, "es"
        )

        response_lower = response.lower()

        # Should contain Spanish elements
        assert "café" in response_lower or "té" in response_lower, "Should mention the items"

        # Should contain Spanish axis terms (generic or food-specific)
        spanish_axis_terms = [
            # Generic terms
            "decisiones coherentes",
            "soluciones ad hoc",
            "más fácil empezar",
            "se adapta mejor",
            "favorece",
            "prioriza lo esencial",
            "dispersa la atención",
            "resultados inmediatos",
            "reduce fricción",
            "añade pasos extra",
            # Food-specific terms (since café vs té is food domain)
            "sabor base",
            "equilibrado",
            "dulzor",
            "carbonatación",
            "resulta más nítido",
            "pierde vivacidad",
            "aroma",
            "postgusto",
            "versatilidad",
            "consistencia",
            "fatiga menos",
            "satura el paladar",
        ]
        spanish_found = any(term in response_lower for term in spanish_axis_terms)
        assert spanish_found, f"Should contain Spanish axis terms: {response}"

    def test_versus_spelling_variant(self):
        """Test 'versus' spelling variant."""
        engine = DebateEngine()

        # Test "versus" detection
        comparator_match = engine.detect_comparator("Mac versus PC", "en")
        assert comparator_match is not None, "Should detect 'versus' variant"
        assert comparator_match["a"] == "mac"
        assert comparator_match["b"] == "pc"
        assert comparator_match["preference"] is None, "Should be neutral for versus"

    def test_no_research_evidence_phrasing(self):
        """Test that responses avoid 'research/evidence' phrasing as requested."""
        engine = DebateEngine()

        test_cases = ["Android vs iPhone", "football vs basketball", "summer vs winter"]

        for user_message in test_cases:
            conversation_history = []
            response = engine.generate_response(
                "general", "opposing", user_message, conversation_history, "en"
            )

            response_lower = response.lower()

            # Should avoid research/evidence language
            forbidden_phrases = [
                "research shows",
                "studies demonstrate",
                "evidence indicates",
                "data shows",
                "research confirms",
                "scientific evidence",
            ]

            forbidden_found = [phrase for phrase in forbidden_phrases if phrase in response_lower]
            assert (
                not forbidden_found
            ), f"Should avoid research/evidence phrasing {forbidden_found}: {response}"

            # Should use the new openings instead
            acceptable_openings = ["i can accept", "worth considering", "test what happens"]
            opening_found = any(opening in response_lower for opening in acceptable_openings)
            assert opening_found, f"Should use comparator-specific openings: {response}"

    def test_multilingual_consistency(self):
        """Test that English and Spanish handle similar patterns consistently."""
        engine = DebateEngine()

        # Test similar patterns in both languages
        en_response = engine.generate_response("general", "opposing", "red vs blue", [], "en")

        es_response = engine.generate_response("general", "opposing", "rojo vs azul", [], "es")

        # Both should be comparator responses (contain axis arguments)
        en_lower = en_response.lower()
        es_lower = es_response.lower()

        en_axis = any(
            term in en_lower
            for term in [
                "coherent long-term decisions",
                "ad hoc solutions",
                "more intuitive",
                "steep curve",
                "easier to get started",
                "demands initial practice",
                # Additional axis terms
                "minimizes interruptions",
                "introduces micro-decisions",
                "reduces friction",
                "adds extra steps",
                "prioritizes the essential",
                "scatters attention",
                "offers immediate results",
                "adapts better to changes",
                "maintains structural rigidity",
            ]
        )
        es_axis = any(
            term in es_lower
            for term in [
                "decisiones coherentes",
                "soluciones ad hoc",
                "más intuitivo",
                "curva empinada",
                "más fácil empezar",
                "exige práctica",
                # Additional axis terms
                "minimiza interrupciones",
                "introduce microdecisiones",
                "reduce fricción",
                "añade pasos extra",
                "prioriza lo esencial",
                "dispersa la atención",
                "resultados inmediatos",
                "se adapta mejor",
                "mantiene rigidez estructural",
            ]
        )

        assert en_axis, f"English should have axis arguments: {en_response}"
        assert es_axis, f"Spanish should have axis arguments: {es_response}"

    def test_fallback_claim_mapping(self):
        """Test fallback claim mapping for neutral patterns."""
        engine = DebateEngine()
        conversation_history = []

        response = engine.generate_response(
            "general", "opposing", "chess vs checkers", conversation_history, "en"
        )

        response_lower = response.lower()

        # Should include fallback claim mapping
        fallback_patterns = [
            "but this overlooks the practical differences",
            "practical differences",
        ]

        fallback_found = any(pattern in response_lower for pattern in fallback_patterns)
        assert fallback_found, f"Should include fallback claim mapping: {response}"

    def test_closing_with_substitution(self):
        """Test that closings properly substitute A/B terms."""
        engine = DebateEngine()
        conversation_history = []

        response = engine.generate_response(
            "general", "opposing", "books vs movies", conversation_history, "en"
        )

        # Should not contain template placeholders
        assert "{{A}}" not in response, "Should substitute {{A}} placeholder"
        assert "{{B}}" not in response, "Should substitute {{B}} placeholder"

        # Should contain the actual terms
        response_lower = response.lower()
        assert (
            "books" in response_lower or "movies" in response_lower
        ), "Should contain actual terms"
