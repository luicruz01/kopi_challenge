"""Tests for food/beverage domain handling in comparator engine."""
from ..handlers import DebateEngine
from ..models import Turn


class TestComparatorFoodDomain:
    def test_coke_vs_pepsi_uses_food_axes_en(self):
        eng = DebateEngine()
        resp = eng.generate_response(
            "general",
            "opposing",
            "explain why Coke is better than Pepsi",
            [],
            "en",
        )

        low = resp.lower()
        # Mentions both
        assert "coke" in low and "pepsi" in low
        # Opposite stance → defend Pepsi
        assert "pepsi" in low
        # Food axes cues (a few representative phrases)
        food_terms = [
            "base flavor",
            "sweetness",
            "carbonation",
            "aromatically",
            "aftertaste",
            "pairing",
            "over repeated sips",
        ]
        assert any(term in low for term in food_terms), resp
        # No unrelated domains
        forbad = ["technology", "research", "evidence", "climate"]
        assert not any(t in low for t in forbad), resp

    def test_color_pair_does_not_use_food_axes_es(self):
        eng = DebateEngine()
        resp = eng.generate_response(
            "general",
            "opposing",
            "El azul es mejor que el rojo",
            [],
            "es",
        )
        low = resp.lower()
        # Should not include food axis lexicon
        food_es_terms = [
            "sabor base",
            "dulzor",
            "carbonatación",
            "aroma",
            "postgusto",
            "cata",
        ]
        assert not any(term in low for term in food_es_terms), resp

    def test_context_persistence_food_axes_followup_es(self):
        eng = DebateEngine()
        conv = []
        # Turn 1 (ES)
        r1 = eng.generate_response(
            "general",
            "opposing",
            "Coca Cola es mejor que Pepsi",
            conv,
            "es",
        )
        conv += [
            Turn(role="user", message="Coca Cola es mejor que Pepsi"),
            Turn(role="bot", message=r1),
        ]

        # Turn 2 follow-up referencing salty foods (still comparator context)
        r2 = eng.generate_response(
            "general",
            "opposing",
            "¿y con comida salada?",
            conv,
            "es",
        )
        low2 = r2.lower()
        # Must remain on coke/pepsi and use food cues
        assert ("coca" in low2 or "cola" in low2) and "pepsi" in low2, r2
        food_es_terms = ["sabor", "carbonatación", "postgusto", "aroma", "versatilidad"]
        assert any(term in low2 for term in food_es_terms), r2

    def test_no_repetition_consecutive_food_open_close_axes(self):
        eng = DebateEngine()
        conv = []
        # 3 turns on the same pair
        msgs = [
            "explain why Coke is better than Pepsi",
            "what?",
            "give me an example",
        ]
        prev = None
        for m in msgs:
            resp = eng.generate_response("general", "opposing", m, conv, "en")
            conv += [Turn(role="user", message=m), Turn(role="bot", message=resp)]
            low = resp.lower()
            if prev is not None:
                # ensure some axis/opening/closing phrase differs to avoid consecutive repetition
                assert prev != resp
            prev = resp
