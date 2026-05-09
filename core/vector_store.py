"""
Thin FAISS wrapper for similarity search over user review embeddings.
"""
from __future__ import annotations
import numpy as np
import faiss


class VectorStore:
    def __init__(self, dim: int):
        self.dim = dim
        self.index = faiss.IndexFlatL2(dim)
        self.metadata: list[dict] = []

    def add(self, vectors: np.ndarray, meta: list[dict]):
        assert vectors.shape[1] == self.dim
        self.index.add(vectors.astype('float32'))
        self.metadata.extend(meta)

    def search(self, query: np.ndarray, k: int = 5) -> list[dict]:
        query = query.astype('float32').reshape(1, -1)
        distances, indices = self.index.search(query, k)
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:
                continue
            result = dict(self.metadata[idx])
            result['score'] = float(dist)
            results.append(result)
        return results

    def __len__(self):
        return self.index.ntotal
