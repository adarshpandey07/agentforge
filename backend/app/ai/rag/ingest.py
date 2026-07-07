"""RAG ingestion: load → chunk → embed → upsert into the vector store."""
from __future__ import annotations

import hashlib
from typing import Union

from .chunker import chunk_text
from .embeddings import embed_texts
from .loaders import load_source
from .stores import get_store


async def ingest_source(
    kb_id: str,
    source_type: str,
    content: Union[bytes, str],
    metadata: dict,
) -> dict:
    """Ingest one source into knowledge base ``kb_id``.

    Returns ``{"chunks": int, "status": "indexed"}`` (contract shape),
    plus ``vector_store`` for observability.
    """
    metadata = dict(metadata or {})
    text = load_source(source_type, content)
    chunks = chunk_text(text, chunk_size=int(metadata.get("chunk_size", 800)),
                        overlap=int(metadata.get("overlap", 100)))
    if not chunks:
        return {"chunks": 0, "status": "empty", "vector_store": "n/a"}

    vectors = await embed_texts(chunks, model=metadata.get("embedding_model", "text-embedding-3-small"))
    doc_key = metadata.get("document_id") or hashlib.md5(
        (source_type + text[:512]).encode("utf-8", errors="replace")
    ).hexdigest()[:12]

    records = [
        {
            "id": f"{kb_id}:{doc_key}:{i}",
            "text": chunk,
            "vector": vec,
            "metadata": {**metadata, "source_type": source_type, "chunk_index": i},
        }
        for i, (chunk, vec) in enumerate(zip(chunks, vectors))
    ]
    store = get_store(metadata.get("vector_store"))
    stored = await store.upsert(kb_id, records)
    return {"chunks": stored, "status": "indexed", "vector_store": store.name}
