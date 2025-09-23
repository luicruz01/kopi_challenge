"""Test claim mapping for better refutations."""
import pytest

from ..handlers import DebateEngine
from ..models import Turn


class TestClaimMapping:
    """Test claim mapping functionality for standardized refutations."""

    def test_spanish_claim_mapping(self):
        """Test Spanish claim mapping patterns."""
        engine = DebateEngine()
        lang = "es"

        test_cases = [
            {
                "input": "Esto es completamente subjetivo",
                "expected": "Tu argumento central es que carece de evidencia científica",
            },
            {
                "input": "No hay evidencia científica que lo respalde",
                "expected": "Tu argumento central es que carece de evidencia científica",
            },
            {
                "input": "Es una perdida de tiempo total",
                "expected": "Tu argumento central es que es un uso inútil del tiempo",
            },
            {
                "input": "Esto no es importante para nada",
                "expected": "Tu argumento central es que no es importante",
            },
            {
                "input": "Es muy caro y costoso",
                "expected": "Tu argumento central es que es muy costoso",
            },
            {
                "input": "Esto no funciona en absoluto",
                "expected": "Tu argumento central es que no funciona",
            },
            {
                "input": "Es peligroso y dañino",
                "expected": "Tu argumento central es que es peligroso o dañino",
            },
        ]

        for test_case in test_cases:
            mapped_claim = engine.map_claim(test_case["input"], lang)
            assert mapped_claim == test_case["expected"], (
                f"Expected '{test_case['expected']}' but got '{mapped_claim}' "
                f"for input '{test_case['input']}'"
            )

    def test_english_claim_mapping(self):
        """Test English claim mapping patterns."""
        engine = DebateEngine()
        lang = "en"

        test_cases = [
            {
                "input": "This is completely subjective",
                "expected": "Your main claim is that it lacks scientific evidence",
            },
            {
                "input": "There's no scientific evidence for this",
                "expected": "Your main claim is that it lacks scientific evidence",
            },
            {
                "input": "It's a complete waste of time",
                "expected": "Your main claim is that it's a waste of time",
            },
            {
                "input": "This is not important at all",
                "expected": "Your main claim is that it's not important",
            },
            {
                "input": "It's too expensive and costly",
                "expected": "Your main claim is that it's too expensive",
            },
            {
                "input": "This doesn't work effectively",
                "expected": "Your main claim is that it doesn't work",
            },
            {
                "input": "It's dangerous and harmful",
                "expected": "Your main claim is that it's dangerous or harmful",
            },
        ]

        for test_case in test_cases:
            mapped_claim = engine.map_claim(test_case["input"], lang)
            assert mapped_claim == test_case["expected"], (
                f"Expected '{test_case['expected']}' but got '{mapped_claim}' "
                f"for input '{test_case['input']}'"
            )

    def test_claim_mapping_fallback(self):
        """Test that unmapped claims fall back to original extraction logic."""
        engine = DebateEngine()

        for lang in ["en", "es"]:
            # Use a message that doesn't match any patterns
            if lang == "es":
                test_message = "Me gusta mucho el color azul y creo que es hermoso"
                expected_fallback = True  # Should extract longest clause
            else:
                test_message = "I really like the color blue and think it's beautiful"
                expected_fallback = True

            mapped_claim = engine.map_claim(test_message, lang)

            # Should fall back to extract_claim logic
            original_claim = engine.extract_claim(test_message, lang)
            assert mapped_claim == original_claim, (
                f"Fallback not working for {lang}: got '{mapped_claim}', "
                f"expected '{original_claim}'"
            )

    def test_claim_mapping_in_responses(self):
        """Test that claim mapping is used in actual response generation."""
        engine = DebateEngine()

        # Test Spanish
        conversation_history = []
        user_message_es = "Creo que la espiritualidad es subjetiva y no tiene evidencia científica"
        user_turn = Turn(role="user", message=user_message_es, sequence=1)
        conversation_history.append(user_turn)

        response_es = engine._generate_unconventional_topic_response(
            "opposing", user_message_es, conversation_history, "es"
        )

        # Should contain the mapped claim about scientific evidence
        assert (
            "carece de evidencia científica" in response_es
        ), f"Spanish claim mapping not used in response: {response_es}"

        # Test English
        conversation_history = []
        user_message_en = "I think spirituality is subjective and lacks scientific evidence"
        user_turn = Turn(role="user", message=user_message_en, sequence=1)
        conversation_history.append(user_turn)

        response_en = engine._generate_unconventional_topic_response(
            "opposing", user_message_en, conversation_history, "en"
        )

        # Should contain the mapped claim about scientific evidence
        assert (
            "lacks scientific evidence" in response_en
        ), f"English claim mapping not used in response: {response_en}"

    def test_claim_mapping_in_topic_responses(self):
        """Test claim mapping in topic-specific responses."""
        engine = DebateEngine()

        # Test with technology topic and "waste of time" claim
        for lang in ["en", "es"]:
            conversation_history = []

            if lang == "es":
                user_message = "La tecnología es una perdida de tiempo"
                expected_claim = "es un uso inútil del tiempo"
            else:
                user_message = "Technology is a waste of time"
                expected_claim = "it's a waste of time"

            user_turn = Turn(role="user", message=user_message, sequence=1)
            conversation_history.append(user_turn)

            response = engine.generate_response(
                "technology", "supporting", user_message, conversation_history, lang
            )

            # Should use mapped claim in refutation
            assert (
                expected_claim in response
            ), f"Claim mapping not used in {lang} topic response: {response}"

    def test_case_insensitive_matching(self):
        """Test that claim mapping works with different cases."""
        engine = DebateEngine()

        test_cases = [
            ("SUBJECTIVE AND UNSCIENTIFIC", "en"),
            ("subjective and unscientific", "en"),
            ("Subjective And Unscientific", "en"),
            ("SUBJETIVO Y SIN EVIDENCIA", "es"),
            ("subjetivo y sin evidencia", "es"),
            ("Subjetivo Y Sin Evidencia", "es"),
        ]

        for message, lang in test_cases:
            mapped_claim = engine.map_claim(message, lang)

            if lang == "en":
                expected = "Your main claim is that it lacks scientific evidence"
            else:
                expected = "Tu argumento central es que carece de evidencia científica"

            assert (
                mapped_claim == expected
            ), f"Case-insensitive matching failed for '{message}' in {lang}: got '{mapped_claim}'"

    def test_partial_pattern_matching(self):
        """Test that patterns match within longer sentences."""
        engine = DebateEngine()

        # Test patterns within complex sentences
        test_cases = [
            {
                "message": "I believe that this approach is completely subjective and lacks any real scientific foundation",
                "lang": "en",
                "expected": "Your main claim is that it lacks scientific evidence",
            },
            {
                "message": "En mi opinión personal, esto es muy subjetivo y no tiene evidencia científica sólida",
                "lang": "es",
                "expected": "Tu argumento central es que carece de evidencia científica",
            },
        ]

        for test_case in test_cases:
            mapped_claim = engine.map_claim(test_case["message"], test_case["lang"])
            assert (
                mapped_claim == test_case["expected"]
            ), f"Partial pattern matching failed for '{test_case['message']}': got '{mapped_claim}'"
