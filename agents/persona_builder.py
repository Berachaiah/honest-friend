"""
Persona Builder — the heart of the system.
Takes a user's review history and extracts a rich behavioural persona.
"""
from __future__ import annotations
import statistics
from core.nigerian_voice import detect_price_sensitivity


def build_persona(reviews: list[dict]) -> dict:
    """
    Analyse a list of review dicts and return a structured persona.

    Each review dict should have: stars, text, date, business_id
    Returns a persona dict used by both Task A and Task B agents.
    """
    if not reviews:
        return _empty_persona()

    stars = [r['stars'] for r in reviews]
    texts = [r['text'] for r in reviews]

    avg_rating = sum(stars) / len(stars)
    rating_std = statistics.stdev(stars) if len(stars) > 1 else 0

    # Rating style
    if avg_rating >= 4.2:
        rating_style = 'generous'
    elif avg_rating <= 2.5:
        rating_style = 'critical'
    else:
        rating_style = 'balanced'

    # Verbosity — median word count
    word_counts = [len(t.split()) for t in texts]
    median_words = statistics.median(word_counts)
    if median_words > 150:
        verbosity = 'detailed'
    elif median_words > 60:
        verbosity = 'moderate'
    else:
        verbosity = 'brief'

    # Sentiment polarity (simple heuristic)
    positive_words = {'great', 'excellent', 'love', 'amazing', 'best', 'fantastic', 'perfect'}
    negative_words = {'terrible', 'awful', 'horrible', 'worst', 'bad', 'disgusting', 'never'}
    pos_count = sum(1 for t in texts for w in t.lower().split() if w in positive_words)
    neg_count = sum(1 for t in texts for w in t.lower().split() if w in negative_words)
    total_words = sum(word_counts)
    sentiment_bias = 'positive' if pos_count > neg_count else ('negative' if neg_count > pos_count else 'neutral')

    # Top categories (requires business metadata; fallback to empty)
    categories = [r.get('business_category', '') for r in reviews if r.get('business_category')]
    top_categories = _top_n(categories, n=3)

    # Price sensitivity from text analysis
    price_sensitivity = detect_price_sensitivity(texts)

    # Consistency — does rating variance suggest a picky reviewer?
    consistency = 'consistent' if rating_std < 1.0 else 'variable'

    # Sample review excerpts (first 100 chars of top 3 reviews by usefulness)
    sorted_reviews = sorted(reviews, key=lambda r: r.get('useful', 0), reverse=True)
    excerpts = [r['text'][:200] for r in sorted_reviews[:3]]

    return {
        'user_id': reviews[0].get('user_id', 'unknown'),
        'review_count': len(reviews),
        'avg_rating': round(avg_rating, 2),
        'rating_style': rating_style,       # generous | balanced | critical
        'verbosity': verbosity,              # brief | moderate | detailed
        'sentiment_bias': sentiment_bias,   # positive | neutral | negative
        'price_sensitivity': price_sensitivity,  # low | medium | high
        'consistency': consistency,         # consistent | variable
        'top_categories': top_categories,
        'sample_excerpts': excerpts,
        'rating_std': round(rating_std, 2),
    }


def persona_to_prompt_block(persona: dict) -> str:
    """Format persona as a detailed, opinionated block for LLM prompts."""
    rating_desc = {
        'generous': f"gives high ratings easily — their average is {persona['avg_rating']}/5",
        'balanced': f"rates fairly — their average is {persona['avg_rating']}/5, neither too harsh nor too kind",
        'critical': f"has very high standards — their average is only {persona['avg_rating']}/5. IMPORTANT: this means they judge quality harshly, NOT that they always complain about price. A ₦500 meal can impress them if it delivers."
    }.get(persona['rating_style'], f"rates around {persona['avg_rating']}/5 on average")

    verbosity_desc = {
        'brief': "writes short, punchy reviews — usually 2-4 sentences",
        'moderate': "writes medium-length reviews — a solid paragraph",
        'detailed': "writes long, thorough reviews — breaks down every aspect"
    }.get(persona['verbosity'], "writes moderate length reviews")

    price_desc = {
        'high': "watches money carefully — always comments on whether price matches value",
        'medium': "notices price but isn't obsessed — mentions it when it stands out",
        'low': "rarely mentions price — focuses on experience and quality instead"
    }.get(persona['price_sensitivity'], "moderate price awareness")

    excerpts_block = ""
    if persona.get('sample_excerpts'):
        excerpts_block = "\nACTUAL WORDS FROM THIS USER'S PAST REVIEWS (use these to understand their voice):\n"
        for i, excerpt in enumerate(persona['sample_excerpts'], 1):
            excerpts_block += f'{i}. "{excerpt[:300]}"\n'
        excerpts_block += "\nSTUDY these excerpts carefully — they reveal what this person actually cares about.\n"

    return f"""
USER PERSONA PROFILE:
- Rating behaviour: This user {rating_desc}
- Writing style: {verbosity_desc}
- Emotional tone: Tends toward {persona['sentiment_bias']} language
- Price awareness: {price_desc}
- Consistency: {persona['consistency']} — {"ratings cluster tightly" if persona['consistency'] == 'consistent' else "ratings vary widely depending on experience"}
- Categories reviewed: {', '.join(persona['top_categories']) if persona['top_categories'] else 'varied, no strong pattern'}
- Reviews analysed: {persona['review_count']}

CRITICAL RULE — PRICE LOGIC:
The product price given is the ONLY price that matters. Do not invent prices.
- Very cheap price (under ₦1,000): NEVER call it expensive. Complain about quality or portions if needed, not cost.
- Very expensive price (above ₦20,000): Even a generous user will acknowledge the cost.
- A CRITICAL user means HIGH STANDARDS for quality — not that everything is overpriced.
- A HIGH price sensitivity means they notice value — not that they always find things too expensive.
{excerpts_block}""".strip()



def _top_n(items: list, n: int = 3) -> list:
    from collections import Counter
    if not items:
        return []
    return [item for item, _ in Counter(items).most_common(n)]


def _empty_persona() -> dict:
    return {
        'user_id': 'new_user',
        'review_count': 0,
        'avg_rating': 3.0,
        'rating_style': 'balanced',
        'verbosity': 'moderate',
        'sentiment_bias': 'neutral',
        'price_sensitivity': 'medium',
        'consistency': 'consistent',
        'top_categories': [],
        'sample_excerpts': [],
        'rating_std': 0,
    }
