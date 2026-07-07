"""RAG retrieval: embed query → similarity search in the vector store."""
from __future__ import annotations

from .embeddings import embed_texts
from .stores import get_store


async def retrieve(kb_id: str, query: str, k: int = 5) -> list[dict]:
    """Return top-``k`` chunks: ``[{"text", "score", "metadata"}, ...]``."""
    if not query:
        return []
    qvec = (await embed_texts([query]))[0]
    store = get_store()
    results = await store.query(kb_id, qvec, k=k)
    # If the configured store is empty/unreachable, also try the in-memory one.
    if not results and store.name != "memory":
        from .stores import NumpyStore

        results = await NumpyStore().query(kb_id, qvec, k=k)
    return results
