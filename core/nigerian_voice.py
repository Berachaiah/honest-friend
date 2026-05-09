"""
Nigerian cultural + linguistic layer.
Injects local context into prompts and post-processes outputs
to feel authentically Nigerian — not cosmetically.
"""

NAIJA_EXPRESSIONS = {
    'very_good':  ["e dey sweet die", "this one na 10/10", "abeg no miss am", "e too correct"],
    'good':       ["e dey okay", "e cool sha", "i go rate am well", "solid experience"],
    'average':    ["e manage", "nothing to write home about", "e dey do", "average at best"],
    'bad':        ["e disappoint me", "them waste my time", "e no dey at all", "I expected better"],
    'very_bad':   ["total rubbish", "e waste my money", "dem cheat person", "avoid am abeg"],
    'expensive':  ["e too cost", "dem wan collect all my money", "price no make sense"],
    'recommend':  ["my guy try am", "abeg no miss this one", "I go send people there"],
    'no_recommend': ["I no go go back", "save your money", "e no worth am"],
}

PRICE_SENSITIVITY_MARKERS = [
    "e too cost", "for this price", "value for money", "worth it",
    "dem overcharge", "affordable", "cost me", "₦", "naira", "budget",
    "expensive", "cheap", "overpriced", "reasonable", "price"
]


def inject_nigerian_context(base_prompt: str, persona: dict) -> str:
    """
    Appends strong Nigerian context instructions to any LLM prompt.
    """
    price_note = ""
    if persona.get('price_sensitivity') == 'high':
        price_note = "- This user mentions price in almost every review. They will absolutely comment on whether the value was worth it — and they are not shy about calling out overpricing.\n"
    elif persona.get('price_sensitivity') == 'medium':
        price_note = "- This user notices price but doesn't obsess over it. They'll mention it if it stands out.\n"

    verbosity_note = ""
    if persona.get('verbosity') == 'brief':
        verbosity_note = "- This user writes SHORT reviews — 2 to 4 sentences max. Do not write an essay.\n"
    elif persona.get('verbosity') == 'detailed':
        verbosity_note = "- This user writes LONG, detailed reviews — they break down every aspect of the experience.\n"

    rating_note = ""
    if persona.get('rating_style') == 'critical':
        rating_note = "- This user is a TOUGH rater. They rarely give 5 stars. A 3 from them is actually a compliment.\n"
    elif persona.get('rating_style') == 'generous':
        rating_note = "- This user is generous with stars. They tend to see the positive side unless something really went wrong.\n"

    naija_instructions = f"""
CULTURAL CONTEXT — READ THIS CAREFULLY:
You are writing as a Nigerian. This means:
- Price sensitivity is real: Nigerians calculate value consciously. "E too cost" is a legitimate complaint even if the food is good.
- Community trust matters: "My friend recommended it" or "people dey talk about am" carries real weight.
- Directness is valued: Nigerians don't sugarcoat. If service was bad, they say it plainly.
- Pidgin appears naturally: It's not forced. It shows up in moments of strong emotion — frustration, excitement, disbelief.
- Specific beats generic: Real reviews mention the actual dish, the actual wait time, the actual staff attitude.
- The ending matters: Nigerian reviews often end with a clear verdict — "I go return" or "dem won't see me again."

USER-SPECIFIC NOTES:
{price_note}{verbosity_note}{rating_note}
"""
    return base_prompt + naija_instructions


def naija_rating_to_words(rating: float) -> str:
    """Convert numeric rating to Nigerian-flavoured descriptor."""
    if rating >= 4.5:
        return NAIJA_EXPRESSIONS['very_good'][0]
    elif rating >= 3.5:
        return NAIJA_EXPRESSIONS['good'][0]
    elif rating >= 2.5:
        return NAIJA_EXPRESSIONS['average'][0]
    elif rating >= 1.5:
        return NAIJA_EXPRESSIONS['bad'][0]
    else:
        return NAIJA_EXPRESSIONS['very_bad'][0]


def detect_price_sensitivity(reviews: list[str]) -> str:
    """
    Analyse review texts to determine how price-sensitive this user is.
    Returns 'high', 'medium', or 'low'.
    """
    hits = sum(
        1 for review in reviews
        for marker in PRICE_SENSITIVITY_MARKERS
        if marker.lower() in review.lower()
    )
    ratio = hits / max(len(reviews), 1)
    if ratio > 0.3:
        return 'high'
    elif ratio > 0.1:
        return 'medium'
    return 'low'