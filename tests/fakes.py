"""Test-only fakes shared across the rag/ test suite."""

import hashlib

from chromadb import EmbeddingFunction


class FakeEmbeddingFunction(EmbeddingFunction):
    """Deterministic, offline stand-in for a real embedding model.

    Used only in tests so the suite never downloads a model or hits the
    network - production ingestion (rag/ingest.py) uses Chroma's real default
    embedding function unless one is passed in explicitly.
    """

    def __init__(self, dim: int = 16):
        self.dim = dim

    def __call__(self, input):
        vectors = []
        for text in input:
            digest = hashlib.sha256(text.encode("utf-8")).digest()
            vectors.append([digest[i % len(digest)] / 255.0 for i in range(self.dim)])
        return vectors

    @staticmethod
    def name():
        return "fake-embedding-function"

    def get_config(self):
        return {"dim": self.dim}

    @staticmethod
    def build_from_config(config):
        return FakeEmbeddingFunction(dim=config.get("dim", 16))
