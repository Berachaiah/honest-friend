"""
Task B — Recommendation Agent.
Cross-domain: Food/Venues, Movies, Books, Music.
Detects domain from context and routes to the right catalogue.
"""
from __future__ import annotations
from agents.persona_builder import build_persona, persona_to_prompt_block
from core.llm import generate
from core.nigerian_voice import inject_nigerian_context
import re

# ── Catalogues ────────────────────────────────────────────────────────────────

FOOD_CATALOGUE = [
    {"id": "1",  "name": "Nkoyo Restaurant",       "category": "Nigerian Fine Dining",    "avg_rating": 4.6, "avg_price": "₦6,000",   "description": "Upscale Nigerian restaurant on Lagos Island serving refined versions of local classics — egusi, ofe akwu, pepper soup. Beautiful interior, excellent service."},
    {"id": "2",  "name": "Terra Kulture",           "category": "Arts/Culture/Food",       "avg_rating": 4.5, "avg_price": "₦4,000",   "description": "Nigerian arts centre on Victoria Island with a restaurant, live theatre, art exhibitions, and a bookshop. Perfect for a cultured outing."},
    {"id": "3",  "name": "Bogobiri House",          "category": "Bar/Lounge/Music",        "avg_rating": 4.4, "avg_price": "₦5,000",   "description": "Intimate boutique guesthouse and bar on Ikoyi with live music, art, and a warm atmosphere. One of Lagos's most beloved hidden gems."},
    {"id": "4",  "name": "Chicken Republic",        "category": "Fast Food",               "avg_rating": 3.5, "avg_price": "₦2,500",   "description": "Reliable Nigerian fast food chain. Consistent quality, quick service, widely available across Lagos."},
    {"id": "5",  "name": "Craft Grill",             "category": "Grill/Bar",               "avg_rating": 4.3, "avg_price": "₦8,000",   "description": "Popular bar and grill in Victoria Island known for suya, grilled fish, cocktails, and a lively weekend crowd."},
    {"id": "6",  "name": "Kilimanjaro Restaurant",  "category": "Nigerian Food",           "avg_rating": 4.1, "avg_price": "₦3,500",   "description": "Well-known Nigerian fast-casual chain serving jollof rice, grilled chicken, and local soups. Reliable and affordable."},
    {"id": "7",  "name": "The Wheatbaker Hotel Bar","category": "Upscale Bar/Lounge",      "avg_rating": 4.5, "avg_price": "₦10,000+", "description": "Sophisticated hotel bar in Ikoyi with premium cocktails, a quiet ambiance, and impeccable service. Best for special occasions."},
    {"id": "8",  "name": "Freedom Park Lagos",      "category": "Outdoor/Culture/Food",    "avg_rating": 4.3, "avg_price": "₦2,000",   "description": "Historic outdoor venue on Lagos Island with food vendors, live music events, art installations, and a relaxed open-air atmosphere."},
    {"id": "9",  "name": "Bukka Hut",               "category": "Nigerian Food",           "avg_rating": 4.2, "avg_price": "₦2,500",   "description": "Popular casual Nigerian restaurant chain. Solid local food — amala, ewedu, gbegiri — at fair prices. Always busy, always consistent."},
    {"id": "10", "name": "Hard Rock Cafe Lagos",    "category": "Bar/International Food",  "avg_rating": 4.0, "avg_price": "₦9,000",   "description": "International bar and restaurant on Eti-Osa with burgers, cocktails, live music, and a buzzing weekend atmosphere."},
]

MOVIE_CATALOGUE = [
    {"id": "m1",  "name": "A Tribe Called Judah",     "category": "Nollywood / Thriller",      "avg_rating": 4.7, "avg_price": "Free (Netflix)", "description": "Gritty Nollywood heist thriller following a desperate mother and her sons. Gripping, raw, and very Nigerian."},
    {"id": "m2",  "name": "Oppenheimer",               "category": "Historical Drama",           "avg_rating": 4.6, "avg_price": "Streaming",      "description": "Christopher Nolan's epic biographical drama about the father of the atomic bomb. Dense, intelligent, visually stunning."},
    {"id": "m3",  "name": "The Burial of Kojo",        "category": "Ghanaian Drama / Art Film",  "avg_rating": 4.4, "avg_price": "Free (Netflix)", "description": "Poetic Ghanaian film about brotherhood, betrayal, and the spirit world. Quietly devastating and visually beautiful."},
    {"id": "m4",  "name": "Parasite",                  "category": "Korean Thriller / Drama",    "avg_rating": 4.8, "avg_price": "Streaming",      "description": "Bong Joon-ho's Oscar-winning masterpiece about class, greed, and deception. No spoilers — just watch it."},
    {"id": "m5",  "name": "Citation",                  "category": "Nollywood / Drama",          "avg_rating": 4.2, "avg_price": "Free (Netflix)", "description": "Nigerian drama about a student who fights back against a professor who assaulted her. Bold, important, and well-made."},
    {"id": "m6",  "name": "Everything Everywhere All at Once", "category": "Sci-Fi / Drama / Comedy", "avg_rating": 4.7, "avg_price": "Streaming", "description": "Chaotic, emotional, and wildly inventive multiverse film. Will make you laugh and cry in the same minute."},
    {"id": "m7",  "name": "Lionheart",                 "category": "Nollywood / Family Drama",   "avg_rating": 4.0, "avg_price": "Free (Netflix)", "description": "Genevieve Nnaji's directorial debut — a warm Nigerian family business drama. First Nigerian film submitted for Academy Awards."},
    {"id": "m8",  "name": "Past Lives",                "category": "Romance / Drama",            "avg_rating": 4.5, "avg_price": "Streaming",      "description": "Quiet, devastating Korean-Canadian romance about two childhood sweethearts separated by immigration. Emotionally precise."},
    {"id": "m9",  "name": "The Woman King",            "category": "Action / Historical Drama",  "avg_rating": 4.4, "avg_price": "Streaming",      "description": "Epic story of the Agojie — the all-female warriors of the Dahomey Kingdom. Viola Davis is extraordinary."},
    {"id": "m10", "name": "Afamefuna: An Nwa Boi Story","category": "Nollywood / Coming of Age", "avg_rating": 4.3, "avg_price": "Streaming",      "description": "Touching Nigerian coming-of-age story about identity, family, and belonging. Quietly powerful."},
]

BOOK_CATALOGUE = [
    {"id": "b1",  "name": "Purple Hibiscus — Chimamanda Ngozi Adichie",       "category": "Nigerian Fiction",        "avg_rating": 4.7, "avg_price": "₦4,500",  "description": "Coming-of-age story about a teenager navigating a religiously oppressive household in post-colonial Nigeria. Devastating and beautiful."},
    {"id": "b2",  "name": "Half of a Yellow Sun — Chimamanda Ngozi Adichie",  "category": "Historical Fiction",      "avg_rating": 4.8, "avg_price": "₦5,000",  "description": "Epic novel set during the Biafran War. Three intertwined perspectives on love, loss, and the cost of war. Essential reading."},
    {"id": "b3",  "name": "Stay With Me — Ayọ̀bámi Adébáyọ̀",                 "category": "Nigerian Fiction",        "avg_rating": 4.5, "avg_price": "₦4,000",  "description": "Searing novel about a Nigerian marriage crumbling under the pressure of infertility, family expectations, and secrets."},
    {"id": "b4",  "name": "Atomic Habits — James Clear",                       "category": "Self-Help / Productivity","avg_rating": 4.6, "avg_price": "₦6,000",  "description": "Practical, evidence-based guide to building good habits and breaking bad ones. One of the most useful books written in the last decade."},
    {"id": "b5",  "name": "Things Fall Apart — Chinua Achebe",                 "category": "Nigerian Classic",        "avg_rating": 4.7, "avg_price": "₦3,000",  "description": "The definitive Nigerian novel. The story of Okonkwo and the collision between Igbo culture and colonialism. Required reading for any African."},
    {"id": "b6",  "name": "Demon Copperhead — Barbara Kingsolver",             "category": "Literary Fiction",        "avg_rating": 4.5, "avg_price": "₦7,000",  "description": "Pulitzer Prize-winning retelling of David Copperfield set in the opioid-ravaged American South. Gripping and compassionate."},
    {"id": "b7",  "name": "The Alchemist — Paulo Coelho",                      "category": "Philosophical Fiction",   "avg_rating": 4.3, "avg_price": "₦3,500",  "description": "Short, philosophical novel about following your dreams. Polarising — some find it profound, others find it simplistic. Worth forming your own opinion."},
    {"id": "b8",  "name": "Educated — Tara Westover",                          "category": "Memoir",                  "avg_rating": 4.7, "avg_price": "₦5,500",  "description": "Extraordinary memoir about a woman who grows up in a survivalist family with no formal education and eventually earns a PhD from Cambridge."},
    {"id": "b9",  "name": "Anxious People — Fredrik Backman",                  "category": "Humour / Drama",          "avg_rating": 4.4, "avg_price": "₦5,000",  "description": "Funny and touching Swedish novel about a failed bank robbery that traps a group of strangers at an apartment viewing. Warm and life-affirming."},
    {"id": "b10", "name": "Freshwater — Akwaeke Emezi",                        "category": "Nigerian Literary Fiction","avg_rating": 4.4, "avg_price": "₦4,500",  "description": "Startlingly original debut novel about an Igbo woman inhabited by multiple spirits (ogbanje). Mythic, personal, and unlike anything else."},
]

MUSIC_CATALOGUE = [
    {"id": "s1",  "name": "Asake — Lungu Boy",              "category": "Afrobeats / Street-Hop",  "avg_rating": 4.6, "avg_price": "Streaming", "description": "Asake's street-hop energy at its finest. Raw, Lagos-coded, irresistibly catchy. For when you want something that feels like the city."},
    {"id": "s2",  "name": "Burna Boy — I Told Them",        "category": "Afrofusion",              "avg_rating": 4.7, "avg_price": "Streaming", "description": "Burna Boy's most confident album. Blends Afrobeats, dancehall, and rap with effortless swagger. 'Tested, Approved & Trusted' is a standout."},
    {"id": "s3",  "name": "Tems — Born in the Wild",        "category": "Afropop / R&B",           "avg_rating": 4.5, "avg_price": "Streaming", "description": "Tems goes global with her debut album — soulful, atmospheric, and deeply personal. 'Me & U' will stay with you."},
    {"id": "s4",  "name": "Wizkid — Morayo",                "category": "Afrobeats",               "avg_rating": 4.4, "avg_price": "Streaming", "description": "Wizkid's love letter to his roots. Warm, melodic, and nostalgic — like a Sunday afternoon in Lagos."},
    {"id": "s5",  "name": "Davido — Timeless",              "category": "Afrobeats",               "avg_rating": 4.5, "avg_price": "Streaming", "description": "Davido's most mature album. Features some of his best songwriting — 'Away', 'Feel', and 'Unavailable' are all certified bangers."},
    {"id": "s6",  "name": "Fela Kuti — Expensive Shit",     "category": "Afrobeat / Classic",      "avg_rating": 4.9, "avg_price": "Streaming", "description": "Fela at his most confrontational and brilliant. If you haven't heard Fela, start here. A reminder that Nigerian music has always been political."},
    {"id": "s7",  "name": "Rema — Heis",                    "category": "Afrobeats / Pop",         "avg_rating": 4.5, "avg_price": "Streaming", "description": "Rema's genre-blending follow-up to 'Calm Down'. Confident, experimental, and full of hooks. Shows he's not a one-hit wonder."},
    {"id": "s8",  "name": "Ayra Starr — The Year I Turned 21","category": "Afropop / R&B",         "avg_rating": 4.6, "avg_price": "Streaming", "description": "Ayra Starr's second album is intimate and bold. She writes about love, heartbreak, and growing up with rare emotional honesty."},
    {"id": "s9",  "name": "Adekunle Gold — Tequila Ever After","category": "Afropop / Soul",       "avg_rating": 4.4, "avg_price": "Streaming", "description": "Smooth, sophisticated, and deeply romantic. AG Baby does his best work when he's in his feelings — this album is proof."},
    {"id": "s10", "name": "Yemi Alade — Empress",           "category": "Afropop / Highlife",      "avg_rating": 4.3, "avg_price": "Streaming", "description": "Yemi Alade at her most powerful — big vocals, pan-African energy, and irresistible dance rhythms. Feel-good from start to finish."},
]

DOMAIN_CATALOGUES = {
    'food':  FOOD_CATALOGUE,
    'movie': MOVIE_CATALOGUE,
    'book':  BOOK_CATALOGUE,
    'music': MUSIC_CATALOGUE,
}

DOMAIN_KEYWORDS = {
    'movie': ['movie', 'film', 'watch', 'cinema', 'netflix', 'series', 'show', 'nollywood'],
    'book':  ['book', 'read', 'novel', 'fiction', 'literature', 'story', 'author'],
    'music': ['music', 'song', 'album', 'playlist', 'listen', 'artist', 'track', 'stream'],
    'food':  ['eat', 'food', 'restaurant', 'dinner', 'lunch', 'drink', 'bar', 'outing', 'hang', 'chill', 'vibe'],
}

def _detect_domain(context: dict) -> str:
    """Detect recommendation domain from context signals."""
    text = ' '.join([
        context.get('mood', ''),
        context.get('occasion', ''),
        context.get('location', ''),
    ]).lower()

    for domain, keywords in DOMAIN_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return domain
    return 'food'  # default


def recommend(persona: dict, context: dict = None, top_k: int = 3) -> dict:
    """Main Task B entry point."""
    context      = context or {}
    domain       = _detect_domain(context)
    catalogue    = DOMAIN_CATALOGUES[domain]
    domain_label = {'food': 'Lagos venues', 'movie': 'movies', 'book': 'books', 'music': 'music albums'}[domain]

    persona_block = persona_to_prompt_block(persona)
    context_block = _format_context(context)

    catalogue_block = "\n".join([
        f"[{item['id']}] {item['name']} | {item['category']} | {item['avg_price']} | "
        f"Rated {item['avg_rating']}/5 | {item['description']}"
        for item in catalogue
    ])

    base_prompt = f"""
You are The Honest Friend — a sharp, culturally-aware Nigerian recommendation agent.
You don't give generic suggestions. You reason deeply about who this person IS, then match them to what they'll genuinely enjoy.
You speak like a trusted friend — direct, opinionated, warm.
Today you are recommending: {domain_label}.

{persona_block}

{context_block}

AVAILABLE OPTIONS ({domain_label.upper()}):
{catalogue_block}

YOUR TASK — Think and reason like a real friend would:

STEP 1 — ANALYSIS:
Who is this person really? Based on their review history:
- What do they genuinely value?
- What would immediately turn them off?
- What does their current context tell you about what they need right now?
- Be specific — reference actual signals from their persona.

STEP 2 — ELIMINATION:
Which options would this specific person NOT enjoy? List each on its own line starting with "- OptionName:".

STEP 3 — RECOMMENDATION:
Pick exactly {top_k} options. For each one:
- Reference something specific from their persona to justify the pick
- Address their current context and occasion
- Point out ONE honest caveat
- Write like a trusted friend: "My guy, this one is for you because..."
- Use Pidgin naturally at moments of emphasis — not on every sentence
- End each recommendation with a one-line verdict

STEP 4 — VERDICT:
One punchy closing sentence.

Format EXACTLY like this:
ANALYSIS: <deep persona analysis>
FILTERED_OUT:
- Option name: reason why
- Option name: reason why
RECOMMENDATIONS:
1. Name — <personalised reason>
2. Name — <personalised reason>
3. Name — <personalised reason>
VERDICT: <one punchy closing line>

IMPORTANT: Do NOT include item IDs. Just use the name.
IMPORTANT: In FILTERED_OUT, put EACH option on its OWN line starting with "- ".
"""

    prompt = inject_nigerian_context(base_prompt, persona)
    raw_output = generate(prompt, max_tokens=900)
    result = _parse_recommendation_output(raw_output)
    result['domain'] = domain
    result['domain_label'] = domain_label
    return result


def _format_context(context: dict) -> str:
    if not context:
        return ""
    parts = []
    if context.get('mood'):     parts.append(f"Current vibe/occasion: {context['mood']}")
    if context.get('occasion'): parts.append(f"Occasion: {context['occasion']}")
    if context.get('location'): parts.append(f"Location: {context['location']}")
    if context.get('budget'):   parts.append(f"Budget: {context['budget']}")
    if parts:
        return "CURRENT CONTEXT:\n" + "\n".join(f"- {p}" for p in parts)
    return ""


def _parse_recommendation_output(raw: str) -> dict:
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
            if rest: analysis_lines.append(rest)
        elif stripped.startswith('FILTERED_OUT:'):
            current_section = 'filtered'
            rest = stripped.replace('FILTERED_OUT:', '').strip()
            if rest:
                for part in re.split(r'\s+-\s+(?=[A-Z])', rest):
                    if part.strip(): filtered_lines.append('- ' + part.strip().lstrip('- '))
        elif stripped.startswith('RECOMMENDATIONS:'):
            current_section = 'recs'
        elif stripped.startswith('VERDICT:'):
            current_section = 'verdict'
            rest = stripped.replace('VERDICT:', '').strip()
            if rest: verdict = rest
        elif current_section == 'analysis':
            analysis_lines.append(stripped)
        elif current_section == 'filtered':
            for part in re.split(r'\s+-\s+(?=[A-Z])', stripped):
                if part.strip(): filtered_lines.append('- ' + part.strip().lstrip('- '))
        elif current_section == 'recs' and stripped and stripped[0].isdigit():
            cleaned = re.sub(r'^\[\d+\]\s*', '', stripped.lstrip('0123456789. '))
            recs.append(cleaned)
        elif current_section == 'verdict' and not verdict:
            verdict = stripped

    return {
        'reasoning_chain':    ' '.join(analysis_lines) or 'N/A',
        'filtered_explanation': '\n'.join(filtered_lines),
        'recommendations':    recs or [raw],
        'verdict':            verdict,
    }


