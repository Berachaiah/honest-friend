"""
Unit tests for The Honest Friend — Persona Builder
Run: python -m pytest tests/ -v
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── Fixtures ──────────────────────────────────────────────────────────────────

GENEROUS_REVIEWS = [
    {'stars': 5, 'text': 'Absolutely amazing food and service! Best place ever!', 'user_id': 'u1'},
    {'stars': 5, 'text': 'Loved everything about this place. Will definitely return!', 'user_id': 'u1'},
    {'stars': 4, 'text': 'Really great spot. Highly recommend to everyone.', 'user_id': 'u1'},
    {'stars': 5, 'text': 'Outstanding quality, worth every penny. Perfect experience.', 'user_id': 'u1'},
    {'stars': 5, 'text': 'Fantastic atmosphere and wonderful staff. Five stars!', 'user_id': 'u1'},
]

CRITICAL_REVIEWS = [
    {'stars': 1, 'text': 'Terrible service, waited forever, food was cold. Never coming back.', 'user_id': 'u2'},
    {'stars': 2, 'text': 'Overpriced for what you get. My mama cooks better for free.', 'user_id': 'u2'},
    {'stars': 1, 'text': 'Absolute rubbish. Waited 1 hour, food was wrong, staff were rude.', 'user_id': 'u2'},
    {'stars': 2, 'text': 'Disappointing. Expected much better given the price point.', 'user_id': 'u2'},
    {'stars': 1, 'text': 'Would not recommend. Worst experience I have had in years.', 'user_id': 'u2'},
]

BALANCED_REVIEWS = [
    {'stars': 4, 'text': 'Solid spot, service was decent. Prices a bit steep but worth it.', 'user_id': 'u3'},
    {'stars': 3, 'text': 'Average food, nothing special. Would try again on a quieter day.', 'user_id': 'u3'},
    {'stars': 4, 'text': 'Good quality but higher prices deserve more consistency.', 'user_id': 'u3'},
    {'stars': 3, 'text': 'Decent enough. Not the best, not the worst. Middle of the road.', 'user_id': 'u3'},
    {'stars': 4, 'text': 'Pretty good overall. Service was friendly and food was fresh.', 'user_id': 'u3'},
]

PRICE_SENSITIVE_REVIEWS = [
    {'stars': 3, 'text': 'Too expensive for what you get. Not worth the price tag.', 'user_id': 'u4'},
    {'stars': 2, 'text': 'Overpriced and underwhelming. Find somewhere cheaper.', 'user_id': 'u4'},
    {'stars': 3, 'text': 'Good food but steep prices. Budget options are better value.', 'user_id': 'u4'},
    {'stars': 4, 'text': 'Nice place but the bill was a shock. Cost more than expected.', 'user_id': 'u4'},
    {'stars': 3, 'text': 'Decent food but expensive. Would prefer a cheaper alternative.', 'user_id': 'u4'},
]


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestPersonaBuilder:

    def setup_method(self):
        from agents.persona_builder import build_persona
        self.build_persona = build_persona

    def test_generous_rating_style(self):
        persona = self.build_persona(GENEROUS_REVIEWS)
        assert persona['rating_style'] == 'generous', \
            f"Expected 'generous', got '{persona['rating_style']}'"

    def test_critical_rating_style(self):
        persona = self.build_persona(CRITICAL_REVIEWS)
        assert persona['rating_style'] == 'critical', \
            f"Expected 'critical', got '{persona['rating_style']}'"

    def test_balanced_rating_style(self):
        persona = self.build_persona(BALANCED_REVIEWS)
        assert persona['rating_style'] == 'balanced', \
            f"Expected 'balanced', got '{persona['rating_style']}'"

    def test_persona_has_required_keys(self):
        persona = self.build_persona(BALANCED_REVIEWS)
        required_keys = [
            'rating_style', 'avg_rating', 'verbosity',
            'price_sensitivity', 'consistency', 'review_count',
        ]
        for key in required_keys:
            assert key in persona, f"Missing key: {key}"

    def test_avg_rating_is_correct(self):
        persona = self.build_persona(GENEROUS_REVIEWS)
        expected = sum(r['stars'] for r in GENEROUS_REVIEWS) / len(GENEROUS_REVIEWS)
        assert abs(persona['avg_rating'] - expected) < 0.01, \
            f"Expected avg_rating {expected:.2f}, got {persona['avg_rating']:.2f}"

    def test_review_count(self):
        persona = self.build_persona(BALANCED_REVIEWS)
        assert persona['review_count'] == len(BALANCED_REVIEWS), \
            f"Expected {len(BALANCED_REVIEWS)}, got {persona['review_count']}"

    def test_price_sensitivity_detected(self):
        persona = self.build_persona(PRICE_SENSITIVE_REVIEWS)
        assert persona['price_sensitivity'] == 'high', \
            f"Expected 'high' price sensitivity, got '{persona['price_sensitivity']}'"

    def test_excerpts_preserved(self):
        persona = self.build_persona(GENEROUS_REVIEWS)
        assert 'excerpts' in persona, "Persona should include review excerpts"
        assert len(persona['excerpts']) > 0, "Excerpts should not be empty"

    def test_empty_reviews_handled(self):
        persona = self.build_persona([])
        assert persona is not None, "Should handle empty review list gracefully"

    def test_single_review_handled(self):
        persona = self.build_persona([BALANCED_REVIEWS[0]])
        assert persona['review_count'] == 1
        assert persona['rating_style'] in ['generous', 'balanced', 'critical']

    def test_generous_avg_rating_above_threshold(self):
        persona = self.build_persona(GENEROUS_REVIEWS)
        assert persona['avg_rating'] >= 4.2, \
            f"Generous persona avg should be >= 4.2, got {persona['avg_rating']}"

    def test_critical_avg_rating_below_threshold(self):
        persona = self.build_persona(CRITICAL_REVIEWS)
        assert persona['avg_rating'] <= 2.5, \
            f"Critical persona avg should be <= 2.5, got {persona['avg_rating']}"


class TestPersonaConsistency:

    def setup_method(self):
        from agents.persona_builder import build_persona
        self.build_persona = build_persona

    def test_same_reviews_same_persona(self):
        """Persona extraction should be deterministic."""
        p1 = self.build_persona(BALANCED_REVIEWS)
        p2 = self.build_persona(BALANCED_REVIEWS)
        assert p1['rating_style'] == p2['rating_style']
        assert p1['avg_rating'] == p2['avg_rating']

    def test_generous_vs_critical_differ(self):
        """Generous and critical personas should produce different rating styles."""
        generous = self.build_persona(GENEROUS_REVIEWS)
        critical = self.build_persona(CRITICAL_REVIEWS)
        assert generous['rating_style'] != critical['rating_style'], \
            "Generous and critical personas must differ"
        assert generous['avg_rating'] > critical['avg_rating'], \
            "Generous avg rating must exceed critical avg rating"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
