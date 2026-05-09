"""
Task B — Recommendation Agent.
Builds on the persona and recommends the best next experience for this user.
Reasons before recommending — this is what makes it agentic.
"""
from __future__ import annotations
from agents.persona_builder import build_persona, persona_to_prompt_block
from core.llm import generate
from core.nigerian_voice import inject_nigerian_context
import re

SAMPLE_CATALOGUE = [
    {"id": "1", "name": "Nkoyo Restaurant", "category": "Nigerian Fine Dining", "avg_rating": 4.6, "avg_price": "₦6,000", "description": "Upscale Nigerian restaurant on Lagos Island serving refined versions of local classics — egusi, ofe akwu, pepper soup. Beautiful interior, excellent service."},
    {"id": "2", "name": "Terra Kulture", "category": "Arts/Culture/Food", "avg_rating": 4.5, "avg_price": "₦4,000", "description": "Nigerian arts centre on Victoria Island with a restaurant, live theatre, art exhibitions, and a bookshop. Perfect for a cultured outing."},
    {"id": "3", "name": "Bogobiri House", "category": "Bar/Lounge/Music", "avg_rating": 4.4, "avg_price": "₦5,000", "description": "Intimate boutique guesthouse and bar on Ikoyi with live music, art, and a warm atmosphere. One of Lagos's most beloved hidden gems."},
    {"id": "4", "name": "Chicken Republic", "category": "Fast Food", "avg_rating": 3.5, "avg_price": "₦2,500", "description": "Reliable Nigerian fast food chain. Consistent quality, quick service, widely available across Lagos."},
    {"id": "5", "name": "Craft Grill", "category": "Grill/Bar", "avg_rating": 4.3, "avg_price": "₦8,000", "description": "Popular bar and grill in Victoria Island known for suya, grilled fish, cocktails, and a lively weekend crowd."},
    {"id": "6", "name": "Kilimanjaro Restaurant", "category": "Nigerian Food", "avg_rating": 4.1, "avg_price": "₦3,500", "description": "Well-known Nigerian fast-casual chain serving jollof rice, grilled chicken, and local soups. Reliable and affordable."},
    {"id": "7", "name": "The Wheatbaker Hotel Bar", "category": "Upscale Bar/Lounge", "avg_rating": 4.5, "avg_price": "₦10,000+", "description": "Sophisticated hotel bar in Ikoyi with premium cocktails, a quiet ambiance, and impeccable service. Best for special occasions."},
    {"id": "8", "name": "Freedom Park Lagos", "category": "Outdoor/Culture/Food", "avg_rating": 4.3, "avg_price": "₦2,000", "description": "Historic outdoor venue on Lagos Island with food vendors, live music events, art installations, and a relaxed open-air atmosphere."},
    {"id": "9", "name": "Bukka Hut", "category": "Nigerian Food", "avg_rating": 4.2, "avg_price": "₦2,500", "description": "Popular casual Nigerian restaurant chain. Solid local food — amala, ewedu, gbegiri — at fair prices. Always busy, always consistent."},
    {"id": "10", "name": "Hard Rock Cafe Lagos", "category": "Bar/International Food", "avg_rating": 4.0, "avg_price": "₦9,000", "description": "International bar and restaurant on Eti-Osa with burgers, cocktails, live music, and a buzzing weekend atmosphere."},
]


def recommend(persona: dict, context: dict = None, top_k: int = 3) -> dict:
    """
    Main Task B entry point.
    """
    persona_block = persona_to_prompt_block(persona)
    context_block = _format_context(context)

    catalogue_block = "\n".join([
        f"[{item['id']}] {item['name']} | {item['category']} | {item['avg_price']} | "
        f"Rated {item['avg_rating']}/5 | {item['description']}"
        for item in SAMPLE_CATALOGUE
    ])

    base_prompt = f"""
You are The Honest Friend — a sharp, culturally-aware Nigerian recommendation agent.
You don't give generic suggestions. You reason deeply about who this person IS, then match them to what they'll genuinely enjoy.
You speak like a trusted friend who knows Lagos well — direct, opinionated, warm.

{persona_block}

{context_block}

AVAILABLE OPTIONS:
{catalogue_block}

YOUR TASK — Think and reason like a real friend would:

STEP 1 — ANALYSIS:
Who is this person really? Based on their review history:
- What do they genuinely value? (atmosphere? food quality? value for money? unique experiences?)
- What would immediately turn them off?
- What does their current context (mood, budget, occasion) tell you about what they need right now?
- Be specific — don't say "they value quality", say "they've complained about slow service twice and always mention portion size"

STEP 2 — ELIMINATION:
Which options would this specific person NOT enjoy? List each on its own line starting with "- OptionName:".
Example:
- Chicken Republic: Too casual for someone who values atmosphere.
- The Wheatbaker: Way above their budget, would cause guilt not joy.

STEP 3 — RECOMMENDATION:
Pick exactly {top_k} options. For each one, you MUST:
- Quote or paraphrase something specific from their actual review samples to justify the pick
  e.g. "You once said '[excerpt]' — this place gets that right"
- Mention their exact budget and whether this fits comfortably or is a stretch
- Address their specific occasion — catching up with a friend needs atmosphere, not just good food
- Point out ONE potential caveat honestly — no place is perfect
- Write like a trusted friend, not a travel guide: "My guy, this one is for you because..."
- Use Pidgin naturally at moments of emphasis or excitement — not on every sentence
- End each recommendation with a one-line verdict: "Go there. You won't regret am."

STEP 4 — VERDICT:
End with one punchy sentence that captures the overall recommendation energy.
Something like: "For your vibe today, start with [X] — thank me later."

Format EXACTLY like this:
ANALYSIS: <deep persona analysis>
FILTERED_OUT:
- Option name: reason why
- Option name: reason why
RECOMMENDATIONS:
1. Name — <personalised reason referencing their specific persona and context>
2. Name — <personalised reason referencing their specific persona and context>
3. Name — <personalised reason referencing their specific persona and context>
VERDICT: <one punchy closing line>

IMPORTANT: Do NOT include item IDs like [1] or [2] anywhere. Just use the name.
IMPORTANT: In FILTERED_OUT, put EACH option on its OWN line starting with "- ". Do not run them together.
"""

    prompt = inject_nigerian_context(base_prompt, persona)
    raw_output = generate(prompt, max_tokens=900)
    return _parse_recommendation_output(raw_output)


def _format_context(context: dict) -> str:
    if not context:
        return ""
    parts = []
    if context.get('mood'):
        parts.append(f"Current vibe/occasion: {context['mood']}")
    if context.get('occasion'):
        parts.append(f"Occasion: {context['occasion']}")
    if context.get('location'):
        parts.append(f"Location: {context['location']}")
    if context.get('budget'):
        parts.append(f"Budget for today: {context['budget']}")
    if parts:
        return "CURRENT CONTEXT:\n" + "\n".join(f"- {p}" for p in parts)
    return ""


def _parse_recommendation_output(raw: str) -> dict:
    """Parse structured LLM output into clean recommendation dict."""
    lines = raw.strip().split('\n')
    analysis_lines, filtered_lines, recs, verdict = [], [], [], ''

    current_section = None

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        if stripped.startswith('ANALYSIS:'):
            current_section = 'analysis'
            rest = stripped.replace('ANALYSIS:', '').strip()
            if rest:
                analysis_lines.append(rest)
        elif stripped.startswith('FILTERED_OUT:'):
            current_section = 'filtered'
            rest = stripped.replace('FILTERED_OUT:', '').strip()
            if rest:
                # LLM may put all items on one line — split them
                parts = re.split(r'\s+-\s+(?=[A-Z])', rest)
                for part in parts:
                    if part.strip():
                        filtered_lines.append('- ' + part.strip().lstrip('- '))
        elif stripped.startswith('RECOMMENDATIONS:'):
            current_section = 'recs'
        elif stripped.startswith('VERDICT:'):
            current_section = 'verdict'
            rest = stripped.replace('VERDICT:', '').strip()
            if rest:
                verdict = rest
        elif current_section == 'analysis':
            analysis_lines.append(stripped)
        elif current_section == 'filtered':
            # Split inline items the LLM runs together on one line
            parts = re.split(r'\s+-\s+(?=[A-Z])', stripped)
            for part in parts:
                if part.strip():
                    filtered_lines.append('- ' + part.strip().lstrip('- '))
        elif current_section == 'recs' and stripped and stripped[0].isdigit():
            cleaned = stripped.lstrip('0123456789. ')
            cleaned = re.sub(r'^\[\d+\]\s*', '', cleaned)
            recs.append(cleaned)
        elif current_section == 'verdict' and not verdict:
            verdict = stripped

    return {
        'reasoning_chain': ' '.join(analysis_lines) or 'N/A',
        'filtered_explanation': '\n'.join(filtered_lines),
        'recommendations': recs or [raw],
        'verdict': verdict,
    }