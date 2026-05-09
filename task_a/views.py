"""Task A views — review generation (web UI + REST API)."""
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
from agents.review_agent import generate_review

def index(request):
    """Landing page / home."""
    return render(request, 'core/index.html')


@csrf_exempt
@require_http_methods(["POST"])
def generate_review_view(request):
    """Web form POST handler for review generation."""
    try:
        data = json.loads(request.body)
        reviews_raw = data.get('reviews', [])
        product = data.get('product', {})

        if not product.get('name'):
            return JsonResponse({'error': 'Product name is required'}, status=400)

        persona = build_persona(reviews_raw)
        result = generate_review(persona, product)

        return JsonResponse({
            'success': True,
            'persona': persona,
            'result': {
                'review': result.get('review', ''),
                'rating': result.get('rating', 3.0),
                'reasoning_chain': result.get('reasoning_chain') or 'Agent reasoning not captured',
                'confidence': result.get('confidence', {}),
                'naija_descriptor': result.get('naija_descriptor', ''),
            },
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


class GenerateReviewAPIView(APIView):
    """
    REST API endpoint for Task A.

    POST /api/task-a/api/generate/
    Body: {
        "reviews": [...],   # list of user's past review dicts
        "product": {
            "name": "...",
            "category": "...",
            "description": "...",
            "avg_price": "..."
        }
    }
    """
    def post(self, request):
        reviews_raw = request.data.get('reviews', [])
        product = request.data.get('product', {})

        if not product.get('name'):
            return Response(
                {'error': 'product.name is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        persona = build_persona(reviews_raw)
        result = generate_review(persona, product)

        return Response({
            'persona': persona,
            'simulated_review': result.get('review'),
            'predicted_rating': result.get('rating'),
            'confidence': result.get('confidence'),
            'reasoning_chain': result.get('reasoning_chain') or 'Agent reasoning not captured',
            'naija_descriptor': result.get('naija_descriptor', ''),
        }, status=status.HTTP_200_OK)
