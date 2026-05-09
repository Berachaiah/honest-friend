"""
Sentence embedding utility.
Lazy-loads the model on first call so startup is fast.
"""
from __future__ import annotations
import numpy as np
from django.conf import settings


_model = None


def get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _model


def embed_texts(texts: list[str]) -> np.ndarray:
    """Return (N, D) float32 array of embeddings."""
    model = get_model()
    return model.encode(texts, convert_to_numpy=True, show_progress_bar=False)


def embed_single(text: str) -> np.ndarray:
    """Return (D,) embedding for one string."""
    return embed_texts([text])[0]
