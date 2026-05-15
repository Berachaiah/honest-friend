"""Task B views — personalised recommendation (web UI + REST API)."""
from __future__ import annotations
import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from agents.persona_builder import build_persona
from agents.recommend_agent import recommend
from agents.cold_start import build_cold_start_persona


@csrf_exempt
@require_http_methods(["POST"])
def recommend_view(request):
    """Web form POST for recommendation — supports multiturn via followup field."""
    try:
        data = json.loads(request.body)
        reviews_raw        = data.get('reviews', [])
        context            = data.get('context', {})
        cold_start_answers = data.get('cold_start_answers')
        followup           = data.get('followup', '').strip()
        history            = data.get('history', [])  # list of prior turns

        if cold_start_answers:
            persona = build_cold_start_persona(cold_start_answers)
        else:
            persona = build_persona(reviews_raw)

        # Multiturn: inject prior conversation + followup into context
        if followup:
            context['followup'] = followup
        if history:
            context['conversation_history'] = history

        result = recommend(persona, context=context)

        return JsonResponse({
            'success': True,
            'persona': persona,
            'result': result,
            'multiturn': bool(followup or history),
            'persona_display': {
                'rating_style':    persona.get('rating_style', 'balanced'),
                'avg_rating':      persona.get('avg_rating', 3.0),
                'verbosity':       persona.get('verbosity', 'moderate'),
                'sentiment_bias':  persona.get('sentiment_bias', 'neutral'),
                'price_sensitivity': persona.get('price_sensitivity', 'medium'),
                'consistency':     persona.get('consistency', 'consistent'),
                'top_categories':  persona.get('top_categories', []),
                'review_count':    persona.get('review_count', 0),
                'rating_std':      persona.get('rating_std', 0),
            }
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


class RecommendAPIView(APIView):
    """
    REST API endpoint for Task B — supports multiturn conversations.

    POST /api/task-b/api/recommend/
    Body: {
        "reviews": [...],
        "context": {
            "mood": "...", "occasion": "...", "location": "...", "budget": "..."
        },
        "followup": "Actually I am vegetarian, refine your recommendations",
        "history": [
            {"turn": 1, "user": "catching up with a friend", "recommendations": ["Terra Kulture", "Bogobiri"]},
            {"turn": 1, "agent_verdict": "Start with Terra Kulture — thank me later."}
        ],
        "cold_start_answers": { ... }
    }
    """
    def post(self, request):
        reviews_raw        = request.data.get('reviews', [])
        context            = request.data.get('context', {})
        cold_start_answers = request.data.get('cold_start_answers')
        followup           = request.data.get('followup', '').strip()
        history            = request.data.get('history', [])

        if cold_start_answers:
            persona = build_cold_start_persona(cold_start_answers)
        else:
            persona = build_persona(reviews_raw)

        if followup:
            context['followup'] = followup
        if history:
            context['conversation_history'] = history

        result = recommend(persona, context=context)

        return Response({
            'persona_summary': {
                'rating_style':      persona['rating_style'],
                'verbosity':         persona['verbosity'],
                'price_sensitivity': persona['price_sensitivity'],
            },
            'recommendations':      result.get('recommendations', []),
            'reasoning_chain':      result.get('reasoning_chain', ''),
            'filtered_explanation': result.get('filtered_explanation', ''),
            'verdict':              result.get('verdict', ''),
            'multiturn':            bool(followup or history),
            'domain':               result.get('domain', 'food'),
        }, status=status.HTTP_200_OK)
