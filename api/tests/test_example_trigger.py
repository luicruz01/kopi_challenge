"""Test example triggering when user requests examples."""
import pytest

from ..handlers import DebateEngine
from ..models import Turn


class TestExampleTrigger:
    """Test example inclusion when triggered by keywords."""

    def test_example_inclusion_spanish(self):
        """Test that Spanish example keywords trigger example inclusion."""
        engine = DebateEngine()
        lang = "es"

        test_cases = [
            "Dame un ejemplo de esto",
            "¿Podrías dar un ejemplo?",
            "Por ejemplo, ¿qué significa esto?",
            "Necesito ejemplos concretos",
        ]

        for user_message in test_cases:
            conversation_history = []
            user_turn = Turn(role="user", message=user_message, sequence=1)
            conversation_history.append(user_turn)

            # Test with unconventional topic (general fallback)
            response = engine._generate_unconventional_topic_response(
                "opposing", user_message, conversation_history, lang
            )

            # Check that an example phrase is included
            example_indicators = ["Por ejemplo", "Un ejemplo concreto", "Un caso", "Considera"]

            has_example = any(indicator in response for indicator in example_indicators)
            assert has_example, f"No example found in response for '{user_message}': {response}"

    def test_example_inclusion_english(self):
        """Test that English example keywords trigger example inclusion."""
        engine = DebateEngine()
        lang = "en"

        test_cases = [
            "Give me an example of this",
            "Can you provide an example?",
            "For example, what does this mean?",
            "I need concrete examples",
        ]

        for user_message in test_cases:
            conversation_history = []
            user_turn = Turn(role="user", message=user_message, sequence=1)
            conversation_history.append(user_turn)

            # Test with unconventional topic (general fallback)
            response = engine._generate_unconventional_topic_response(
                "opposing", user_message, conversation_history, lang
            )

            # Check that an example phrase is included
            example_indicators = ["For example", "A concrete case", "A clear case", "Consider"]

            has_example = any(indicator in response for indicator in example_indicators)
            assert has_example, f"No example found in response for '{user_message}': {response}"

    def test_topic_specific_examples(self):
        """Test that topic-specific examples are used when available."""
        engine = DebateEngine()

        # Test with technology topic
        for lang in ["en", "es"]:
            conversation_history = []

            if lang == "es":
                user_message = "Dame un ejemplo sobre tecnología"
                topic = "technology"
                expected_topics = ["automatización", "redes sociales", "algoritmos"]
            else:
                user_message = "Give me an example about technology"
                topic = "technology"
                expected_topics = ["automation", "social media", "algorithms"]

            user_turn = Turn(role="user", message=user_message, sequence=1)
            conversation_history.append(user_turn)

            # Use the main generate_response method to get topic-specific response
            response = engine.generate_response(
                topic, "opposing", user_message, conversation_history, lang
            )

            # Check that response includes topic-relevant examples
            has_topic_example = any(
                topic_word in response.lower() for topic_word in expected_topics
            )
            assert (
                has_topic_example
            ), f"No topic-specific example found in {lang} response: {response}"

    def test_no_example_without_trigger(self):
        """Test that examples are not included when not requested."""
        engine = DebateEngine()

        for lang in ["en", "es"]:
            conversation_history = []

            if lang == "es":
                user_message = "Creo que la tecnología es mala"
            else:
                user_message = "I think technology is bad"

            user_turn = Turn(role="user", message=user_message, sequence=1)
            conversation_history.append(user_turn)

            response = engine.generate_response(
                "technology", "opposing", user_message, conversation_history, lang
            )

            # Should not contain example indicators unless naturally part of content
            forced_example_indicators = [
                "For example" if lang == "en" else "Por ejemplo",
                "A concrete case" if lang == "en" else "Un ejemplo concreto",
            ]

            # Count example indicators - should be minimal/none for non-example requests
            example_count = sum(
                1 for indicator in forced_example_indicators if indicator in response
            )

            # Allow at most 1 naturally occurring example phrase
            assert (
                example_count <= 1
            ), f"Too many example indicators without trigger in {lang}: {response}"

    def test_example_rotation(self):
        """Test that examples rotate to avoid repetition."""
        engine = DebateEngine()
        lang = "en"
        topic = "general"

        conversation_history = []
        responses = []

        # Generate multiple responses requesting examples
        for i in range(3):
            user_message = f"Give me an example {i}"
            user_turn = Turn(
                role="user", message=user_message, sequence=len(conversation_history) + 1
            )
            conversation_history.append(user_turn)

            response = engine._generate_unconventional_topic_response(
                "opposing", user_message, conversation_history, lang
            )
            responses.append(response)

            bot_turn = Turn(role="bot", message=response, sequence=len(conversation_history) + 1)
            conversation_history.append(bot_turn)

        # Extract example sentences from responses
        examples = []
        for response in responses:
            # Look for example sentences
            sentences = response.split(". ")
            for sentence in sentences:
                if (
                    "For example" in sentence
                    or "Consider how" in sentence
                    or "A concrete case" in sentence
                ):
                    examples.append(sentence.strip())
                    break

        # Should have different examples (rotation working)
        unique_examples = set(examples)
        assert len(unique_examples) > 1, f"Examples not rotating: {examples}"

    def test_deterministic_example_selection(self):
        """Test that example selection is deterministic."""
        engine = DebateEngine()

        for lang in ["en", "es"]:
            conversation_history = []
            user_message = "Give me an example" if lang == "en" else "Dame un ejemplo"

            response1 = engine._generate_unconventional_topic_response(
                "opposing", user_message, conversation_history, lang
            )

            response2 = engine._generate_unconventional_topic_response(
                "opposing", user_message, conversation_history, lang
            )

            assert response1 == response2, f"Example selection not deterministic for {lang}"
