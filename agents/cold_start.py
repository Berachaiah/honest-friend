"""
Cold Start Handler.
For users with no history — builds a lightweight persona from targeted questions
or sensible defaults, then routes to the normal agents.
"""
from __future__ import annotations
from agents.persona_builder import _empty_persona


COLD_START_QUESTIONS = [
    "How strict are you with ratings? (1 = I give 5 stars easily / 5 = I only give 5 if it's perfect)",
    "What do you care about most when trying somewhere new? (e.g. price, quality, atmosphere, convenience)",
    "Give me 2-3 things you love and 2-3 things you hate in any experience.",
]


def build_cold_start_persona(answers: dict) -> dict:
    """
    Build a persona from cold-start questionnaire answers.

    answers: {
        'rating_strictness': int (1-5),
        'priorities': list[str],
        'loves': list[str],
        'hates': list[str],
        'price_budget': str (optional)
    }
    """
    persona = _empty_persona()
    persona['user_id'] = 'cold_start_user'

    strictness = answers.get('rating_strictness', 3)
    if strictness <= 2:
        persona['rating_style'] = 'generous'
        persona['avg_rating'] = 4.2
    elif strictness >= 4:
        persona['rating_style'] = 'critical'
        persona['avg_rating'] = 2.8
    else:
        persona['rating_style'] = 'balanced'
        persona['avg_rating'] = 3.5

    priorities = answers.get('priorities', [])
    if 'price' in str(priorities).lower() or 'budget' in str(priorities).lower():
        persona['price_sensitivity'] = 'high'

    loves = answers.get('loves', [])
    hates = answers.get('hates', [])
    persona['sample_excerpts'] = [
        f"Things I love: {', '.join(loves)}",
        f"Things I hate: {', '.join(hates)}",
    ]
    persona['cold_start'] = True

    return persona
