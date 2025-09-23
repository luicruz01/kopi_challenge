"""Chat handlers with deterministic debate engine."""
import re
from uuid import uuid4

from fastapi import HTTPException

from .lexicon import CLOSING_PHRASES, CONTENT_BANKS, LANGUAGE_MARKERS, REASONING_PHRASES, TOPIC_DATA
from .models import ChatRequest, ChatResponse, Turn
from .storage import ConversationStore
from .utils import stable_index


class DebateEngine:
    """Deterministic local debate engine with multilingual support."""

    def __init__(self):
        # Import lexicon data
        self.content_banks = CONTENT_BANKS
        self.reasoning_phrases = REASONING_PHRASES
        self.closing_phrases = CLOSING_PHRASES
        self.topic_data = TOPIC_DATA

    def detect_lang(self, text: str) -> str:
        """Detect language using simple heuristics - returns 'es' or 'en'."""
        text_lower = text.lower()

        # Check for Spanish accents first (strong indicator)
        has_accents = any(char in text for char in "áéíóúüñ¿¡")
        if has_accents:
            return "es"

        # Get language-specific words from lexicon
        spanish_specific = LANGUAGE_MARKERS["es"]["specific_words"]
        english_specific = LANGUAGE_MARKERS["en"]["specific_words"]

        # Count language-specific words
        spanish_count = sum(
            1 for word in spanish_specific if " " + word + " " in " " + text_lower + " "
        )
        english_count = sum(
            1 for word in english_specific if " " + word + " " in " " + text_lower + " "
        )

        # If we have clear indicators for one language, use it
        if spanish_count >= 2 and spanish_count > english_count:
            return "es"
        if english_count >= 2 and english_count > spanish_count:
            return "en"

        # Fallback: check for common patterns
        spanish_patterns = LANGUAGE_MARKERS["es"]["patterns"]
        english_patterns = LANGUAGE_MARKERS["en"]["patterns"]

        has_spanish_pattern = any(pattern in text_lower for pattern in spanish_patterns)
        has_english_pattern = any(pattern in text_lower for pattern in english_patterns)

        if has_spanish_pattern and not has_english_pattern:
            return "es"
        if has_english_pattern and not has_spanish_pattern:
            return "en"

        # Final fallback - if uncertain, default to English
        return "en"

    def detect_stance(self, text: str, lang: str) -> str:
        """Detect user stance using rule-based heuristics - returns 'pro' or 'contra'."""
        text_lower = text.lower()

        # Get stance indicators from lexicon
        markers = LANGUAGE_MARKERS[lang]
        negation_markers = markers["negation_markers"]
        contra_indicators = markers["contra_indicators"]
        pro_indicators = markers["pro_indicators"]

        # Count negation markers
        negation_count = sum(1 for marker in negation_markers if marker in text_lower)

        # Count stance indicators
        contra_count = sum(1 for indicator in contra_indicators if indicator in text_lower)
        pro_count = sum(1 for indicator in pro_indicators if indicator in text_lower)

        # Determine stance based on indicators and negations
        # High negation + pro words often means contra stance
        if negation_count >= 2 and pro_count > 0:
            return "contra"

        # Direct contra indicators
        if contra_count > pro_count:
            return "contra"

        # Pro indicators outweigh contra
        if pro_count > contra_count:
            return "pro"

        # Fallback: look for overall sentiment with negation context
        if negation_count > 0:
            return "contra"

        # Final fallback - assume pro stance (most common)
        return "pro"

    def extract_topic_and_stance(self, message: str, lang: str = "en") -> tuple[str, str]:
        """Extract topic and determine bot's stance (always opposite of user)."""
        message_lower = message.lower()

        topics = self.topic_data[lang]

        detected_topic = "general"
        for topic, data in topics.items():
            if any(keyword in message_lower for keyword in data["keywords"]):
                detected_topic = topic
                break

        # Detect user's stance, then take opposite for debate
        user_stance = self.detect_stance(message, lang)

        # Bot always takes opposite stance for engaging debate
        if user_stance == "pro":
            bot_stance = "opposing"
        else:
            bot_stance = "supporting"

        return detected_topic, bot_stance

    def extract_claim(self, text: str, lang: str) -> str:
        """Extract a key claim from user text for refutation."""
        # Split into clauses by punctuation
        clauses = re.split(r"[.?!;]", text.strip())

        if not clauses:
            return "su punto" if lang == "es" else "your point"

        # Find longest clause
        longest_clause = max(clauses, key=len).strip()

        if not longest_clause:
            return "su punto" if lang == "es" else "your point"

        # Remove filler phrases
        if lang == "es":
            fillers = [
                "creo que",
                "pienso que",
                "me parece que",
                "en mi opinión",
                "según",
                "para mí",
            ]
        else:
            fillers = [
                "i think",
                "i believe",
                "it seems",
                "in my opinion",
                "according to",
                "for me",
            ]

        for filler in fillers:
            longest_clause = longest_clause.replace(filler, "").strip()

        # Cap length and clean
        if len(longest_clause) > 200:
            longest_clause = longest_clause[:200] + "..."

        return longest_clause or ("su punto" if lang == "es" else "your point")

    def _get_deterministic_choice(self, options: list[str], seed: str) -> str:
        """Get deterministic choice from options based on seed."""
        index = stable_index(seed, len(options))
        return options[index]

    def _get_rotated_analogy(
        self, analogies: list[str], seed: str, conversation_history: list[Turn]
    ) -> str:
        """Get analogy with rotation to avoid immediate repetition."""
        # Get the base choice
        choice_index = stable_index(seed, len(analogies))

        # Check last bot turn for analogy repetition
        if len(conversation_history) >= 2:
            last_bot_turn = None
            for turn in reversed(conversation_history):
                if turn.role == "bot":
                    last_bot_turn = turn
                    break

            if last_bot_turn:
                current_analogy = analogies[choice_index]
                if current_analogy in last_bot_turn.message:
                    # Rotate to next analogy deterministically
                    choice_index = (choice_index + 1) % len(analogies)

        return analogies[choice_index]

    def detect_topic_switch(self, current_message: str, fixed_topic: str, lang: str) -> str | None:
        """Detect if user switched topics with threshold to avoid false positives."""
        message_lower = current_message.lower()
        topics = self.topic_data[lang]

        # Count keyword matches for each topic
        topic_scores = {}
        for topic, data in topics.items():
            if topic == "general":
                continue
            score = sum(1 for keyword in data["keywords"] if keyword in message_lower)
            if score > 0:
                topic_scores[topic] = score

        # Only switch if we have a strong match (2+ keywords) and it's different from fixed topic
        if topic_scores:
            best_topic = max(topic_scores.keys(), key=lambda t: topic_scores[t])
            if topic_scores[best_topic] >= 2 and best_topic != fixed_topic:
                return best_topic

        return None

    def _get_rotated_phrase(
        self, phrases: list[str], seed: str, conversation_history: list[Turn]
    ) -> str:
        """Get phrase with rotation to avoid immediate repetition."""
        # Get the base choice
        choice_index = stable_index(seed, len(phrases))

        # Check last bot turn for phrase repetition
        if len(conversation_history) >= 2:
            last_bot_turn = None
            for turn in reversed(conversation_history):
                if turn.role == "bot":
                    last_bot_turn = turn
                    break

            if last_bot_turn:
                current_phrase = phrases[choice_index]
                if current_phrase in last_bot_turn.message:
                    # Rotate to next phrase deterministically
                    choice_index = (choice_index + 1) % len(phrases)

        return phrases[choice_index]

    def _generate_unconventional_topic_response(
        self, stance: str, user_message: str, conversation_history: list[Turn], lang: str
    ) -> str:
        """Generate fallback response for unconventional/subjective topics."""
        # Extract subject from user message for context
        claim = self.extract_claim(user_message, lang)

        # Acknowledge subjectivity/atypical nature
        if lang == "es":
            acknowledgment = (
                "Reconozco que se trata de un tema subjetivo y de preferencias personales."
            )
            stance_intro = (
                "Sin embargo, mantengo mi posición de que"
                if stance == "opposing"
                else "Apoyo firmemente que"
            )
        else:
            acknowledgment = "I recognize this is a subjective matter of personal preference."
            stance_intro = (
                "However, I maintain that" if stance == "opposing" else "I firmly support that"
            )

        # Generic but relevant arguments based on stance
        if stance == "opposing":
            if lang == "es":
                generic_args = [
                    "las tradiciones y estándares establecidos tienen valor por una razón",
                    "la consistencia en nuestras elecciones refleja principios sólidos",
                    "no todas las innovaciones o cambios representan mejoras reales",
                ]
            else:
                generic_args = [
                    "established traditions and standards have value for a reason",
                    "consistency in our choices reflects solid principles",
                    "not all innovations or changes represent real improvements",
                ]
        else:
            if lang == "es":
                generic_args = [
                    "la diversidad de opciones enriquece nuestras experiencias",
                    "la apertura a diferentes enfoques fomenta el crecimiento personal",
                    "las preferencias individuales merecen respeto y consideración",
                ]
            else:
                generic_args = [
                    "diversity of options enriches our experiences",
                    "openness to different approaches fosters personal growth",
                    "individual preferences deserve respect and consideration",
                ]

        # Select argument deterministically
        turn_count = len([t for t in conversation_history if t.role == "bot"])
        arg_seed = f"unconventional_{turn_count}_{user_message[:20]}"
        selected_arg = self._get_deterministic_choice(generic_args, arg_seed)

        # Build response
        reasoning_seed = f"unconventional_reasoning_{turn_count}"
        reasoning = self._get_rotated_phrase(
            self.reasoning_phrases[lang], reasoning_seed, conversation_history
        )

        closing_seed = f"unconventional_closing_{turn_count}"
        closing = self._get_rotated_phrase(
            self.closing_phrases[lang], closing_seed, conversation_history
        )

        # Refutation using extracted claim
        if lang == "es":
            refutation = f'Aunque mencionas que "{claim}", esta perspectiva pasa por alto consideraciones importantes.'
        else:
            refutation = (
                f'While you mention "{claim}", this perspective overlooks important considerations.'
            )

        return (
            f"{acknowledgment} {stance_intro} {selected_arg}. En términos generales, {reasoning}. {refutation} {closing}"
            if lang == "es"
            else f"{acknowledgment} {stance_intro} {selected_arg}. Generally speaking, {reasoning}. {refutation} {closing}"
        )

    def generate_response(
        self,
        topic: str,
        stance: str,
        user_message: str,
        conversation_history: list[Turn],
        lang: str = "en",
        metadata: dict = None,
    ) -> str:
        """Generate deterministic multilingual debate response with variety."""
        # Check for unconventional topic fallback first
        if topic == "general":
            return self._generate_unconventional_topic_response(
                stance, user_message, conversation_history, lang
            )

        # Check for topic switch acknowledgment
        topic_switch_ack = ""
        if metadata and len(conversation_history) > 2:  # Not first exchange
            switched_topic = self.detect_topic_switch(user_message, topic, lang)
            if switched_topic:
                topic_names = {
                    "en": {
                        "climate": "climate change",
                        "technology": "technology",
                        "education": "education",
                    },
                    "es": {
                        "climate": "cambio climático",
                        "technology": "tecnología",
                        "education": "educación",
                    },
                }
                fixed_name = topic_names.get(lang, {}).get(topic, topic)
                new_name = topic_names.get(lang, {}).get(switched_topic, switched_topic)

                template = self.content_banks[lang]["topic_switch"]
                topic_switch_ack = template.format(topic_fixed=fixed_name, topic_new=new_name) + " "

        # Use conversation context for deterministic seed
        turn_count = len([t for t in conversation_history if t.role == "bot"])
        seed = f"{topic}_{stance}_{lang}_{turn_count}_{user_message[:30]}"

        # Get topic data
        topic_data = self.topic_data[lang].get(topic, self.topic_data[lang]["general"])
        content_bank = self.content_banks[lang]

        # 1. Anchor - stance assertion with variety
        anchor_options = content_bank["anchors"][stance]
        anchor_seed = f"{seed}_anchor"
        anchor_template = self._get_deterministic_choice(anchor_options, anchor_seed)
        anchor = anchor_template.format(topic=topic)

        # 2. Generate 2 arguments with variety
        arguments = []
        for i in range(2):
            arg_seed = f"{seed}_arg_{i}"
            template = self._get_deterministic_choice(content_bank["arguments"], arg_seed)
            argument = self._get_deterministic_choice(topic_data["arguments"], arg_seed)
            # Use rotated reasoning phrases
            reasoning_seed = f"{seed}_reasoning_{i}"
            reasoning = self._get_rotated_phrase(
                self.reasoning_phrases[lang], reasoning_seed, conversation_history
            )
            arguments.append(template.format(argument=argument, reasoning=reasoning))

        # 3. Generate analogy with rotation
        analogy_seed = f"{seed}_analogy"
        analogy_template = self._get_deterministic_choice(content_bank["analogies"], analogy_seed)
        analogy = self._get_rotated_analogy(
            topic_data["analogies"], analogy_seed, conversation_history
        )
        principle = self._get_deterministic_choice(topic_data["principles"], analogy_seed)
        analogy_text = analogy_template.format(analogy=analogy, principle=principle)

        # 4. Generate question
        question_seed = f"{seed}_question"
        question_template = self._get_deterministic_choice(content_bank["questions"], question_seed)
        question = self._get_deterministic_choice(topic_data["questions"], question_seed)
        question_text = question_template.format(question=question)

        # 5. Better refutation using extracted claim
        refutation_templates = {
            "en": [
                'Your claim that "{claim}" overlooks the broader context.',
                'While you mention "{claim}", this perspective misses key considerations.',
                'The argument that "{claim}" fails to account for important factors.',
            ],
            "es": [
                'Tu afirmación de que "{claim}" pasa por alto el contexto más amplio.',
                'Aunque mencionas que "{claim}", esta perspectiva pierde consideraciones clave.',
                'El argumento de que "{claim}" no tiene en cuenta factores importantes.',
            ],
        }

        refutation_seed = f"{seed}_refutation"
        claim = self.extract_claim(user_message, lang)
        refutation_template = self._get_deterministic_choice(
            refutation_templates[lang], refutation_seed
        )
        refutation = refutation_template.format(claim=claim)

        # 6. Conclusion with rotated phrases
        close_seed = f"{seed}_close"
        conclusion = self._get_rotated_phrase(
            self.closing_phrases[lang], close_seed, conversation_history
        )

        # Combine all parts
        response_parts = (
            [anchor] + arguments + [analogy_text, question_text, refutation, conclusion]
        )
        response_text = " ".join(response_parts)

        # Prepend topic switch acknowledgment if needed
        return topic_switch_ack + response_text


class ChatHandler:
    """Handles chat requests with conversation management."""

    def __init__(self, store: ConversationStore):
        self.store = store
        self.engine = DebateEngine()
        self.conversations_metadata = {}  # {conversation_id: {"topic": str, "stance": str, "lang": str}}

    async def handle_chat(self, request: ChatRequest, request_id: str) -> ChatResponse:
        """Handle chat request with multilingual debate response."""
        # Generate conversation ID if not provided
        if not request.conversation_id:
            conversation_id = str(uuid4())

            # Detect language from first message
            lang = self.engine.detect_lang(request.message)

            # Extract topic and stance from first message
            topic, stance = self.engine.extract_topic_and_stance(request.message, lang)

            self.conversations_metadata[conversation_id] = {
                "topic": topic,
                "stance": stance,
                "lang": lang,
            }

            existing_turns = []
        else:
            conversation_id = request.conversation_id

            # Get existing conversation
            existing_turns = await self.store.get_conversation(conversation_id)
            if existing_turns is None:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error": {
                            "code": "not_found",
                            "message": "Conversation not found",
                            "trace_id": request_id,
                        }
                    },
                )

            # Get metadata for this conversation
            if conversation_id not in self.conversations_metadata:
                # Try to extract from existing turns (fallback)
                if existing_turns:
                    first_user_message = next(
                        (turn.message for turn in existing_turns if turn.role == "user"),
                        request.message,
                    )
                    # Detect language from first user message
                    lang = self.engine.detect_lang(first_user_message)
                    topic, stance = self.engine.extract_topic_and_stance(first_user_message, lang)
                    self.conversations_metadata[conversation_id] = {
                        "topic": topic,
                        "stance": stance,
                        "lang": lang,
                    }
                else:
                    # Fallback - detect from current message
                    lang = self.engine.detect_lang(request.message)
                    self.conversations_metadata[conversation_id] = {
                        "topic": "general",
                        "stance": "opposing",
                        "lang": lang,
                    }

        # Add user message to conversation
        user_turn = Turn(role="user", message=request.message)
        current_turns = existing_turns + [user_turn]

        # Generate bot response
        metadata = self.conversations_metadata[conversation_id]
        bot_message = self.engine.generate_response(
            metadata["topic"],
            metadata["stance"],
            request.message,
            current_turns,
            metadata["lang"],
            metadata,
        )

        # Add bot response
        bot_turn = Turn(role="bot", message=bot_message)
        current_turns.append(bot_turn)

        # Save conversation
        await self.store.save_conversation(conversation_id, current_turns)

        # Return response (storage already trims to last 10)
        final_turns = await self.store.get_conversation(conversation_id)
        return ChatResponse(conversation_id=conversation_id, message=final_turns or current_turns)
