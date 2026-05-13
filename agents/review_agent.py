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

    price = product.get('avg_price', '')
    price_display = price if price and price not in ['₦0', '0', ''] else 'not specified'

    avg = persona.get('avg_rating', 3.0)
    style = persona.get('rating_style', 'balanced')
    if style == 'critical':
        lo, hi = 1.0, 3.0
    elif style == 'generous':
        lo, hi = 3.5, 5.0
    else:
        lo = max(1.0, round(avg - 1.5, 1))
        hi = min(5.0, round(avg + 1.5, 1))

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

2. RATING — You MUST give a rating between {lo} and {hi}.
   This user's historical average is {avg}/5 and their style is {style}.
   A rating outside {lo}–{hi} is factually wrong and unacceptable. Do not do it.

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

CRITICAL FINAL REMINDER: Your RATING must be between {lo} and {hi}. No exceptions.

Format your response EXACTLY like this:
REASONING: <quote from their reviews then your prediction>
RATING: <single number between {lo} and {hi}>
REVIEW: <the simulated review in the user's voice>
"""

    prompt = inject_nigerian_context(base_prompt, persona)
    raw_output = generate(prompt, max_tokens=800)
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
