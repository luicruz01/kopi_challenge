"""Chat handlers with deterministic debate engine."""
import re
from uuid import uuid4

from fastapi import HTTPException

from .lexicon import (
    CLAIM_MAPPINGS,
    CLOSING_PHRASES,
    CONTENT_BANKS,
    EXAMPLE_BANKS,
    LANGUAGE_MARKERS,
    REASONING_PHRASES,
    STRUCTURAL_BANKS,
    TOPIC_DATA,
)
from .lexicon_axes import AXES_EN, AXES_ES, CLOSINGS_EN, CLOSINGS_ES, EXAMPLES_EN, EXAMPLES_ES, OPENINGS_EN, OPENINGS_ES
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
        self.structural_banks = STRUCTURAL_BANKS
        self.example_banks = EXAMPLE_BANKS
        self.claim_mappings = CLAIM_MAPPINGS
        self.axes = {"en": AXES_EN, "es": AXES_ES}
        self.comp_openings = {"en": OPENINGS_EN, "es": OPENINGS_ES}
        self.comp_closings = {"en": CLOSINGS_EN, "es": CLOSINGS_ES}
        self.comp_examples = {"en": EXAMPLES_EN, "es": EXAMPLES_ES}

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

    def map_claim(self, text: str, lang: str) -> str:
        """Map common claim patterns to standardized refutation phrases."""
        text_lower = text.lower()

        # Try to match patterns in claim mappings
        for pattern, mapped_claim in self.claim_mappings[lang].items():
            if re.search(pattern, text_lower):
                return mapped_claim

        # Fallback to original extraction logic
        return self.extract_claim(text, lang)

    def should_include_example(self, text: str, lang: str) -> bool:
        """Check if user message requests an example."""
        text_lower = text.lower()

        if lang == "es":
            example_keywords = ["ejemplo", "ejemplos", "por ejemplo", "dame un ejemplo"]
        else:
            example_keywords = ["example", "examples", "for example", "give me an example"]

        return any(keyword in text_lower for keyword in example_keywords)

    def get_example_sentence(
        self, topic: str, lang: str, seed: str, conversation_history: list[Turn]
    ) -> str:
        """Get an example sentence for the topic with rotation to avoid repetition."""
        examples = self.example_banks[lang].get(topic, self.example_banks[lang]["general"])

        # Get the base choice
        choice_index = stable_index(seed, len(examples), salt="example")

        # Check last bot turn for example repetition
        if len(conversation_history) >= 2:
            last_bot_turn = None
            for turn in reversed(conversation_history):
                if turn.role == "bot":
                    last_bot_turn = turn
                    break

            if last_bot_turn:
                current_example = examples[choice_index]
                if current_example in last_bot_turn.message:
                    # Rotate to next example deterministically
                    choice_index = (choice_index + 1) % len(examples)

        return examples[choice_index]

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

    def _get_rotated_structural_element(
        self, element_type: str, lang: str, seed: str, conversation_history: list[Turn]
    ) -> str:
        """Get structural element (opening, body, closing) with rotation to avoid immediate repetition."""
        elements = self.structural_banks[lang][element_type]

        # Get the base choice
        choice_index = stable_index(seed, len(elements), salt=element_type)

        # Check last bot turn for element repetition
        if len(conversation_history) >= 2:
            last_bot_turn = None
            for turn in reversed(conversation_history):
                if turn.role == "bot":
                    last_bot_turn = turn
                    break

            if last_bot_turn:
                current_element = elements[choice_index]
                if current_element in last_bot_turn.message:
                    # Rotate to next element deterministically
                    choice_index = (choice_index + 1) % len(elements)

        return elements[choice_index]

    def detect_comparator(self, text: str, lang: str) -> dict | None:
        """
        Detect generic comparator patterns (A vs B, A better than B).
        
        Returns:
            dict with {a, b, preference} or None if no comparison detected
            preference ∈ {a, b, None} where None means neutral "A vs B"
        """
        # Normalize text - lowercase, strip punctuation, collapse spaces
        normalized = re.sub(r'[^\w\s]', ' ', text.lower())
        normalized = ' '.join(normalized.split())

        # Define comparison patterns for both languages
        if lang == "es":
            patterns = [
                # "A vs B" or "A contra B" or "A frente a B"
                r'(?P<a>[\w\s-]+?)\s+(?:vs|versus|contra|frente\s+a)\s+(?P<b>[\w\s-]+?)(?:\s|$)',
                # "A es mejor que B" or variations
                r'(?P<a>[\w\s-]+?)\s+(?:es\s*)?(?:mejor|superior)\s*(?:que|a)\s+(?P<b>[\w\s-]+?)(?:\s|$)',
                # "prefiero A a B"
                r'prefiero\s+(?P<a>[\w\s-]+?)\s+a\s+(?P<b>[\w\s-]+?)(?:\s|$)',
            ]
        else:
            patterns = [
                # "A vs B" or "A versus B"
                r'(?P<a>[\w\s-]+?)\s+(?:vs|versus)\s+(?P<b>[\w\s-]+?)(?:\s|$)',
                # "A is better than B" or "A better than B"  
                r'(?P<a>[\w\s-]+?)\s+(?:is\s+)?(?:better|superior)\s*(?:than|to)\s+(?P<b>[\w\s-]+?)(?:\s|$)',
                # "prefer A to B"
                r'prefer\s+(?P<a>[\w\s-]+?)\s+to\s+(?P<b>[\w\s-]+?)(?:\s|$)',
                # More specific patterns to extract the core items
                r'(?:explain\s+why\s+)?(?P<a>[\w\s-]+?)\s+(?:is\s+)?(?:better|superior)\s+than\s+(?P<b>[\w\s-]+?)(?:\s|$)',
            ]

        for pattern in patterns:
            match = re.search(pattern, normalized)
            if match:
                a_raw = match.group('a').strip()
                b_raw = match.group('b').strip()
                
                # Clean up extracted terms
                a = self._clean_comparator_term(a_raw)
                b = self._clean_comparator_term(b_raw)
                
                # Skip if either side is too short or invalid
                if len(a) < 2 or len(b) < 2 or a == b:
                    continue
                
                # Determine preference based on pattern type
                preference = None
                if 'mejor' in pattern or 'better' in pattern or 'superior' in pattern or 'prefer' in pattern:
                    # Patterns that indicate preference for A
                    preference = 'a'
                elif 'vs' in pattern or 'versus' in pattern or 'contra' in pattern or 'frente' in pattern:
                    # Neutral comparison patterns
                    preference = None
                
                return {
                    'a': a,
                    'b': b,
                    'preference': preference
                }
        
        return None

    def _clean_comparator_term(self, term: str) -> str:
        """Clean up extracted comparator terms by removing prefixes and stop words."""
        # Remove common prefixes
        prefixes_to_remove = [
            'explain why', 'why', 'that', 'the', 'a', 'an', 
            'explicar por que', 'por que', 'que', 'el', 'la', 'un', 'una'
        ]
        
        term_lower = term.lower().strip()
        for prefix in prefixes_to_remove:
            if term_lower.startswith(prefix + ' '):
                term = term[len(prefix):].strip()
                term_lower = term.lower().strip()
        
        # Remove trailing articles and common words
        suffixes_to_remove = ['the', 'a', 'an', 'el', 'la', 'un', 'una']
        words = term.split()
        while words and words[-1].lower() in suffixes_to_remove:
            words.pop()
        
        if words:
            return ' '.join(words)
        return term

    def render_comparator_response(
        self, match: dict, user_message: str, conversation_history: list[Turn], lang: str
    ) -> str:
        """
        Render response for generic comparator using axis-based arguments.
        
        Args:
            match: Dict with {a, b, preference} from detect_comparator
            user_message: User's input message
            conversation_history: Conversation history for rotation logic
            lang: Language code (en/es)
        """
        a = match["a"]
        b = match["b"]
        preference = match["preference"]
        
        # Determine sides and stance
        if preference == "a":
            # User prefers A, bot argues for B
            user_side = a
            bot_side = b
        elif preference == "b":
            # User prefers B, bot argues for A
            user_side = b
            bot_side = a
        else:
            # Neutral "A vs B" - choose bot side deterministically
            bot_index = stable_index(f"{a}|{b}", 2)
            if bot_index == 0:
                bot_side = b
                user_side = a
            else:
                bot_side = a
                user_side = b
        
        turn_count = len([t for t in conversation_history if t.role == "bot"])
        seed_base = f"comp_{a[:10]}_{b[:10]}_{turn_count}_{user_message[:20]}"
        
        # 1. Opening
        opening_seed = f"{seed_base}_opening"
        opening_index = stable_index(opening_seed, len(self.comp_openings[lang]), salt="opening")
        
        # Rotate if same as previous turn
        if len(conversation_history) >= 2:
            last_bot_turn = None
            for turn in reversed(conversation_history):
                if turn.role == "bot":
                    last_bot_turn = turn
                    break
            
            if last_bot_turn:
                current_opening = self.comp_openings[lang][opening_index]
                if current_opening in last_bot_turn.message:
                    opening_index = (opening_index + 1) % len(self.comp_openings[lang])
        
        opening = self.comp_openings[lang][opening_index]
        
        # 2. Select 2-3 axes deterministically with rotation
        axes = []
        used_axes = set()
        
        for i in range(min(3, len(self.axes[lang]))):
            axis_seed = f"{seed_base}_axis_{i}"
            axis_index = stable_index(axis_seed, len(self.axes[lang]), salt=f"axis-{i}")
            
            # Avoid consecutive repetition
            if len(conversation_history) >= 2:
                last_bot_turn = None
                for turn in reversed(conversation_history):
                    if turn.role == "bot":
                        last_bot_turn = turn
                        break
                
                if last_bot_turn:
                    current_axis = self.axes[lang][axis_index]
                    if current_axis in last_bot_turn.message:
                        axis_index = (axis_index + 1) % len(self.axes[lang])
            
            # Avoid using the same axis twice in one response
            attempts = 0
            while axis_index in used_axes and attempts < len(self.axes[lang]):
                axis_index = (axis_index + 1) % len(self.axes[lang])
                attempts += 1
            
            used_axes.add(axis_index)
            axis_template = self.axes[lang][axis_index]
            axis_text = axis_template.replace("{{A}}", user_side).replace("{{B}}", bot_side)
            axes.append(axis_text)
        
        # 3. Claim mapping
        claim_refutation = ""
        if preference and ("better" in user_message.lower() or "mejor" in user_message.lower()):
            if lang == "es":
                claim_refutation = f"Tu idea central es que {user_side} supera a {bot_side}; sostengo lo contrario por las razones anteriores."
            else:
                claim_refutation = f"Your core claim is that {user_side} beats {bot_side}; I maintain the opposite for the reasons above."
        else:
            # Fallback to regular claim mapping
            mapped_claim = self.map_claim(user_message, lang)
            claim_refutation = f"{mapped_claim}, but this overlooks the practical differences."
        
        # 4. Example if requested
        example_sentence = ""
        if self.should_include_example(user_message, lang):
            example_seed = f"{seed_base}_example"
            example_index = stable_index(example_seed, len(self.comp_examples[lang]), salt="example")
            example_template = self.comp_examples[lang][example_index]
            example_sentence = " " + example_template.replace("{{A}}", user_side).replace("{{B}}", bot_side)
        
        # 5. Closing
        closing_seed = f"{seed_base}_closing"
        closing_index = stable_index(closing_seed, len(self.comp_closings[lang]), salt="closing")
        
        # Rotate if same as previous turn
        if len(conversation_history) >= 2:
            last_bot_turn = None
            for turn in reversed(conversation_history):
                if turn.role == "bot":
                    last_bot_turn = turn
                    break
            
            if last_bot_turn:
                current_closing = self.comp_closings[lang][closing_index]
                if current_closing in last_bot_turn.message:
                    closing_index = (closing_index + 1) % len(self.comp_closings[lang])
        
        closing_template = self.comp_closings[lang][closing_index]
        closing = closing_template.replace("{{A}}", user_side).replace("{{B}}", bot_side)
        
        # Combine all parts
        axes_text = " ".join(axes)
        return f"{opening}, {axes_text} {claim_refutation}{example_sentence} {closing}"

    def _generate_unconventional_topic_response(
        self, stance: str, user_message: str, conversation_history: list[Turn], lang: str
    ) -> str:
        """Generate fallback response for unconventional/subjective topics with structural variety."""
        turn_count = len([t for t in conversation_history if t.role == "bot"])
        seed_base = f"unconventional_{turn_count}_{user_message[:20]}"

        # 1. Opening with structural variety
        opening_seed = f"{seed_base}_opening"
        opening = self._get_rotated_structural_element(
            "openings", lang, opening_seed, conversation_history
        )

        # 2. Body with structural variety
        body_seed = f"{seed_base}_body"
        body = self._get_rotated_structural_element("bodies", lang, body_seed, conversation_history)

        # 3. Reasoning phrase
        reasoning_seed = f"{seed_base}_reasoning"
        reasoning = self._get_rotated_phrase(
            self.reasoning_phrases[lang], reasoning_seed, conversation_history
        )

        # 4. Better claim refutation using mapping
        mapped_claim = self.map_claim(user_message, lang)

        # Build refutation with mapped claim
        if lang == "es":
            refutation = (
                f"{mapped_claim}, pero esta perspectiva pasa por alto consideraciones importantes."
            )
        else:
            refutation = f"{mapped_claim}, but this perspective overlooks important considerations."

        # 5. Example sentence if requested
        example_sentence = ""
        if self.should_include_example(user_message, lang):
            example_seed = f"{seed_base}_example"
            example_sentence = " " + self.get_example_sentence(
                "general", lang, example_seed, conversation_history
            )

        # 6. Closing with structural variety
        closing_seed = f"{seed_base}_closing"
        closing = self._get_rotated_structural_element(
            "closings", lang, closing_seed, conversation_history
        )

        # Combine all parts with proper sentence structure
        if lang == "es":
            return f"{opening} {body}. En términos generales, {reasoning}. {refutation}{example_sentence} {closing}"
        else:
            return f"{opening} {body}. Generally speaking, {reasoning}. {refutation}{example_sentence} {closing}"

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
        # Check for comparator patterns first (before topic routing and generic fallback)
        comparator_match = self.detect_comparator(user_message, lang)
        if comparator_match:
            return self.render_comparator_response(
                comparator_match, user_message, conversation_history, lang
            )
        
        # Check for unconventional topic fallback
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

        # 5. Better refutation using claim mapping
        refutation_seed = f"{seed}_refutation"
        mapped_claim = self.map_claim(user_message, lang)

        refutation_templates = {
            "en": [
                f"{mapped_claim}, but this overlooks the broader context.",
                f"{mapped_claim}, yet this perspective misses key considerations.",
                f"{mapped_claim}, though this fails to account for important factors.",
            ],
            "es": [
                f"{mapped_claim}, pero esto pasa por alto el contexto más amplio.",
                f"{mapped_claim}, aunque esta perspectiva pierde consideraciones clave.",
                f"{mapped_claim}, pero esto no tiene en cuenta factores importantes.",
            ],
        }

        refutation_template = self._get_deterministic_choice(
            refutation_templates[lang], refutation_seed
        )
        refutation = refutation_template

        # 6. Example sentence if requested
        example_sentence = ""
        if self.should_include_example(user_message, lang):
            example_seed = f"{seed}_example"
            example_sentence = " " + self.get_example_sentence(
                topic, lang, example_seed, conversation_history
            )

        # 7. Conclusion with rotated phrases
        close_seed = f"{seed}_close"
        conclusion = self._get_rotated_phrase(
            self.closing_phrases[lang], close_seed, conversation_history
        )

        # Combine all parts
        response_parts = (
            [anchor]
            + arguments
            + [analogy_text, question_text, refutation + example_sentence, conclusion]
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
