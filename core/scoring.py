"""
Self-evaluation logic.
The agent scores its own output confidence before returning.
"""
from __future__ import annotations


def self_evaluate(review_text: str, persona: dict, predicted_rating: float) -> dict:
    """
    Heuristic confidence scoring — in production this can call the LLM again.
    Returns a confidence dict with score (0-1) and flags.
    """
    flags = []
    score = 1.0

    # Review length matches verbosity expectation
    word_count = len(review_text.split())
    verbosity = persona.get('verbosity', 'moderate')
    if verbosity == 'detailed' and word_count < 80:
        flags.append('review_too_short_for_persona')
        score -= 0.15
    elif verbosity == 'brief' and word_count > 200:
        flags.append('review_too_long_for_persona')
        score -= 0.1

    # Rating in expected range
    avg = persona.get('avg_rating', 3.0)
    std = persona.get('rating_std', 1.0)
    if abs(predicted_rating - avg) > (std * 2 + 1):
        flags.append('rating_out_of_expected_range')
        score -= 0.2

    # Check for generic/placeholder content
    generic_phrases = ['i would recommend', 'overall great experience', 'five stars']
    for phrase in generic_phrases:
        if phrase in review_text.lower():
            flags.append('potentially_generic_output')
            score -= 0.05
            break

    return {
        'score': round(max(0, score), 2),
        'flags': flags,
        'passed': score >= 0.7
    }
