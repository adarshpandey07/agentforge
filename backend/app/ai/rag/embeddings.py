"""Embedding provider: OpenAI when configured, deterministic stub otherwise."""
from __future__ import annotations

import hashlib
import math
import os

STUB_DIM = 256


def _stub_embed(text: str) -> list[float]:
    """Deterministic hash-based embedding (works with zero dependencies).

    Token-hash bag-of-words so similar texts share dimensions.
    """
    vec = [0.0] * STUB_DIM
    for token in text.lower().split():
        h = hashlib.md5(token.encode("utf-8")).digest()
        idx = int.from_bytes(h[:4], "little") % STUB_DIM
        sign = 1.0 if h[4] % 2 == 0 else -1.0
        vec[idx] += sign
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


async def embed_texts(texts: list[str], model: str = "text-embedding-3-small") -> list[list[float]]:
    """Embed texts. Uses OpenAI if OPENAI_API_KEY is set, else the stub."""
    if os.environ.get("OPENAI_API_KEY"):
        try:
            from openai import AsyncOpenAI  # lazy

            client = AsyncOpenAI()
            resp = await client.embeddings.create(model=model, input=texts)
            return [d.embedding for d in resp.data]
        except Exception:
            pass
    return [_stub_embed(t) for t in texts]


def cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(x * x for x in b)) or 1.0
    return dot / (na * nb)
