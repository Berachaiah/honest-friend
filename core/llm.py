"""
LLM interface — uses Groq API for fast Llama 4 Scout inference.
Falls back to a stub response in DEBUG mode if no key is set.
"""
from __future__ import annotations
import requests
from django.conf import settings

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"


def generate(prompt: str, max_tokens: int = 512) -> str:
    """Public interface — generate text from prompt."""
    try:
        return _call_groq(prompt, max_tokens=max_tokens)
    except Exception as e:
        if settings.DEBUG:
            return f"[LLM ERROR - DEBUG MODE]: {str(e)}\n\nStub: {_stub_response(prompt)}"
        raise


def _call_groq(prompt: str, max_tokens: int = 512) -> str:
    """Call Groq API with Llama 4 Scout."""
    api_key = getattr(settings, 'GROQ_API_KEY', '')

    if not api_key:
        return _stub_response(prompt)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": 0.7,
    }
    response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=60)
    response.raise_for_status()

    data = response.json()
    return data['choices'][0]['message']['content'].strip()


def _stub_response(prompt: str) -> str:
    """Stub for local dev without API key."""
    if 'review' in prompt.lower():
        return (
            "Honestly, this place surprised me. The service was solid — "
            "dem actually tried. For the price, e dey okay. "
            "I go give am 4 stars and possibly return. My guy would enjoy am.\n"
            "RATING: 4.0"
        )
    elif 'recommend' in prompt.lower():
        return (
            "ANALYSIS: This user values quality and fair pricing.\n"
            "FILTERED_OUT: None significantly.\n"
            "RECOMMENDATIONS:\n"
            "1. [4] Buka Spot Abuja — Matches their love for authentic, affordable food\n"
            "2. [7] ReadersHub Bookstore — Quiet, quality experience fits their profile\n"
            "3. [2] The Tech Hub Lagos — Aligns with their professional interests"
        )
    return "I don analyse your request and I go give you my honest take soon."