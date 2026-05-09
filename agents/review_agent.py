"""
Task A — Review Generation Agent.
Given a user persona + product details, generates a simulated review and star rating.
"""
from __future__ import annotations
from agents.persona_builder import build_persona, persona_to_prompt_block
from core.llm import generate
from core.nigerian_voice import inject_nigerian_context, naija_rating_to_words
from core.scoring import self_evaluate


def generate_review(persona: dict, product: dict) -> dict:
    
    persona_block = persona_to_prompt_block(persona)

    # Handle missing/zero price BEFORE building the prompt
    price = product.get('avg_price', '')
    price_display = price if price and price not in ['₦0', '0', ''] else 'not specified'

    base_prompt = f"""
You are simulating a review written by a specific Nigerian user. You must sound like a real person — not a robot, not a food blogger, not a customer service form. A real Nigerian with opinions.

{persona_block}

PRODUCT TO REVIEW:
- Name: {product.get('name', 'Unknown')}
- Category: {product.get('category', 'General')}
- Description: {product.get('description', 'No description provided')}
- Price range: {price_display}

IMPORTANT: If the price is "not specified", do NOT invent a price. Never fabricate a specific naira amount.

STRICT INSTRUCTIONS:
1. REASONING — Start by quoting one of this user's actual review samples verbatim (use their exact words).
   Then in 1-2 sentences explain what that quote reveals about how they will react to this product.
   Format: "This user said: '[exact quote]' — this means they will [specific prediction]."
   Do NOT give generic descriptions. Do NOT say "this user tends to..." without a quote first.

2. RATING — Give a star rating (1.0 to 5.0). Be precise. A generous rater gives 4.5 where a critical one gives 2.0.

PRICE LOGIC — CRITICAL RULE:
- Under ₦1,000: NEVER call it expensive. Complain about quality or portions instead.
- Above ₦10,000: Even a generous user acknowledges the cost.
- A critical persona means HIGH STANDARDS, not that everything is overpriced.

3. REVIEW — Write in this user's authentic voice:
   - Sound like a real Nigerian typing a Google review
   - Mix English and Pidgin naturally — only where it flows
   - Be SPECIFIC — mention actual things from the description
   - Be OPINIONATED — clear stance, no fence-sitting
   - Match verbosity — brief user = short review, detailed user = long review
   - Never say "I had a wonderful dining experience"

EXAMPLES OF GOOD NIGERIAN REVIEW VOICE:
- "The chicken was good sha, but make I tell you — waiting 40 minutes for fast food is not it."
- "E too cost for what they give you. My neighbor's buka does better for half the price."
- "Honestly? One of the better spots in Lagos. The jollof alone will make you forget your problems."

Format your response EXACTLY like this:
REASONING: <quote from their reviews then your prediction>
RATING: <single number 1.0 to 5.0>
REVIEW: <the simulated review in the user's voice>
"""

    prompt = inject_nigerian_context(base_prompt, persona)
    raw_output = generate(prompt, max_tokens=800)
    logging.warning(f"RAW LLM OUTPUT:\n{raw_output}")  # add this
    parsed = _parse_output(raw_output)

    confidence = self_evaluate(
        review_text=parsed['review'],
        persona=persona,
        predicted_rating=parsed['rating']
    )
    parsed['confidence'] = confidence
    parsed['naija_descriptor'] = naija_rating_to_words(parsed['rating'])

    return parsed


def _parse_output(raw: str) -> dict:
    """Extract structured fields from LLM output."""
    lines = raw.strip().split('\n')
    reasoning_lines = []
    rating = 3.0
    review = raw
    current_section = None

    for i, line in enumerate(lines):
        if line.startswith('REASONING:'):
            current_section = 'reasoning'
            rest = line.replace('REASONING:', '').strip()
            if rest:
                reasoning_lines.append(rest)
        elif line.startswith('RATING:'):
            current_section = 'rating'
            try:
                rating = float(line.replace('RATING:', '').strip().split()[0])
                rating = max(1.0, min(5.0, rating))
            except ValueError:
                rating = 3.0
        elif line.startswith('REVIEW:'):
            review = '\n'.join(lines[i:]).replace('REVIEW:', '', 1).strip()
            break
        elif current_section == 'reasoning' and line.strip():
            reasoning_lines.append(line.strip())

    reasoning = ' '.join(reasoning_lines) or 'Agent reasoning not captured'

    return {
        'reasoning_chain': reasoning,
        'rating': rating,
        'review': review,
    }