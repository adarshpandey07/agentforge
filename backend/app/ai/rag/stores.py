"""Vector store adapter registry.

``VectorStoreAdapter`` is the ABC; adapters for pgvector, Chroma, Qdrant,
Pinecone and Weaviate lazily import their clients. ``NumpyStore`` is a pure
in-memory fallback that always works (numpy optional). ``get_store`` returns
the requested adapter or transparently falls back to NumpyStore.
"""
from __future__ import annotations

import os
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Callable

from .embeddings import cosine


class VectorStoreAdapter(ABC):
    """Adapter interface all vector stores implement."""

    name: str = "base"

    @abstractmethod
    async def upsert(self, kb_id: str, records: list[dict]) -> int:
        """records: [{"id", "text", "vector", "metadata"}] → count stored."""

    @abstractmethod
    async def query(self, kb_id: str, vector: list[float], k: int = 5) -> list[dict]:
        """→ [{"text", "score", "metadata"}] sorted by similarity desc."""

    async def delete(self, kb_id: str) -> None:  # optional
        return None


# --------------------------------------------------------------------------- #
class NumpyStore(VectorStoreAdapter):
    """In-memory store (module-level so it survives across instances)."""

    name = "memory"
    _data: dict[str, list[dict]] = defaultdict(list)

    async def upsert(self, kb_id: str, records: list[dict]) -> int:
        existing = {r["id"] for r in self._data[kb_id]}
        for r in records:
            if r["id"] in existing:
                self._data[kb_id] = [x for x in self._data[kb_id] if x["id"] != r["id"]]
            self._data[kb_id].append(r)
        return len(records)

    async def query(self, kb_id: str, vector: list[float], k: int = 5) -> list[dict]:
        rows = self._data.get(kb_id, [])
        scored = [
            {"text": r["text"], "score": round(cosine(vector, r["vector"]), 4),
             "metadata": r.get("metadata", {})}
            for r in rows
        ]
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:k]

    async def delete(self, kb_id: str) -> None:
        self._data.pop(kb_id, None)


# --------------------------------------------------------------------------- #
class PgVectorStore(VectorStoreAdapter):
    """pgvector-backed store (default in production)."""

    name = "pgvector"

    async def _conn(self):
        url = os.environ.get("DATABASE_URL", "")
        if not url:
            return None
        try:
            import asyncpg  # lazy

            dsn = url.replace("postgresql+asyncpg://", "postgresql://")
            conn = await asyncpg.connect(dsn, timeout=3)
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            await conn.execute(
                """CREATE TABLE IF NOT EXISTS ai_rag_chunks (
                       id TEXT PRIMARY KEY, kb_id TEXT, text TEXT,
                       metadata JSONB, embedding vector(256))"""
            )
            return conn
        except Exception:
            return None

    async def upsert(self, kb_id: str, records: list[dict]) -> int:
        conn = await self._conn()
        if conn is None:
            return await NumpyStore().upsert(kb_id, records)
        try:
            import json as _json

            for r in records:
                vec = "[" + ",".join(str(round(v, 6)) for v in r["vector"]) + "]"
                await conn.execute(
                    """INSERT INTO ai_rag_chunks (id, kb_id, text, metadata, embedding)
                       VALUES ($1,$2,$3,$4,$5::vector)
                       ON CONFLICT (id) DO UPDATE SET text=$3, metadata=$4, embedding=$5::vector""",
                    r["id"], kb_id, r["text"], _json.dumps(r.get("metadata", {})), vec,
                )
            return len(records)
        except Exception:
            return await NumpyStore().upsert(kb_id, records)
        finally:
            try:
                await conn.close()
            except Exception:
                pass

    async def query(self, kb_id: str, vector: list[float], k: int = 5) -> list[dict]:
        conn = await self._conn()
        if conn is None:
            return await NumpyStore().query(kb_id, vector, k)
        try:
            import json as _json

            vec = "[" + ",".join(str(round(v, 6)) for v in vector) + "]"
            rows = await conn.fetch(
                """SELECT text, metadata, 1 - (embedding <=> $2::vector) AS score
                   FROM ai_rag_chunks WHERE kb_id=$1 ORDER BY embedding <=> $2::vector LIMIT $3""",
                kb_id, vec, k,
            )
            return [
                {"text": r["text"], "score": round(float(r["score"]), 4),
                 "metadata": _json.loads(r["metadata"]) if r["metadata"] else {}}
                for r in rows
            ]
        except Exception:
            return await NumpyStore().query(kb_id, vector, k)
        finally:
            try:
                await conn.close()
            except Exception:
                pass


# --------------------------------------------------------------------------- #
class ChromaStore(VectorStoreAdapter):
    name = "chroma"

    def _coll(self, kb_id: str):
        import chromadb  # lazy

        client = chromadb.PersistentClient(path=os.environ.get("CHROMA_PATH", ".chroma"))
        return client.get_or_create_collection(f"kb_{kb_id}")

    async def upsert(self, kb_id: str, records: list[dict]) -> int:
        try:
            coll = self._coll(kb_id)
            coll.upsert(
                ids=[r["id"] for r in records],
                embeddings=[r["vector"] for r in records],
                documents=[r["text"] for r in records],
                metadatas=[r.get("metadata", {}) or {"_": 1} for r in records],
            )
            return len(records)
        except Exception:
            return await NumpyStore().upsert(kb_id, records)

    async def query(self, kb_id: str, vector: list[float], k: int = 5) -> list[dict]:
        try:
            res = self._coll(kb_id).query(query_embeddings=[vector], n_results=k)
            out = []
            for i, doc in enumerate(res["documents"][0]):
                dist = res["distances"][0][i] if res.get("distances") else 0.0
                meta = res["metadatas"][0][i] if res.get("metadatas") else {}
                out.append({"text": doc, "score": round(1.0 - dist, 4), "metadata": meta})
            return out
        except Exception:
            return await NumpyStore().query(kb_id, vector, k)


class QdrantStore(VectorStoreAdapter):
    name = "qdrant"

    async def upsert(self, kb_id: str, records: list[dict]) -> int:
        try:
            from qdrant_client import QdrantClient  # lazy
            from qdrant_client.models import Distance, PointStruct, VectorParams

            client = QdrantClient(url=os.environ.get("QDRANT_URL", "http://localhost:6333"))
            coll = f"kb_{kb_id}"
            try:
                client.get_collection(coll)
            except Exception:
                client.create_collection(
                    coll, vectors_config=VectorParams(size=len(records[0]["vector"]), distance=Distance.COSINE)
                )
            client.upsert(coll, points=[
                PointStruct(id=abs(hash(r["id"])) % (10 ** 12), vector=r["vector"],
                            payload={"text": r["text"], **(r.get("metadata") or {})})
                for r in records
            ])
            return len(records)
        except Exception:
            return await NumpyStore().upsert(kb_id, records)

    async def query(self, kb_id: str, vector: list[float], k: int = 5) -> list[dict]:
        try:
            from qdrant_client import QdrantClient  # lazy

            client = QdrantClient(url=os.environ.get("QDRANT_URL", "http://localhost:6333"))
            hits = client.search(f"kb_{kb_id}", query_vector=vector, limit=k)
            return [
                {"text": h.payload.get("text", ""), "score": round(float(h.score), 4),
                 "metadata": {kk: vv for kk, vv in h.payload.items() if kk != "text"}}
                for h in hits
            ]
        except Exception:
            return await NumpyStore().query(kb_id, vector, k)


class PineconeStore(VectorStoreAdapter):
    name = "pinecone"

    def _index(self):
        from pinecone import Pinecone  # lazy

        pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
        return pc.Index(os.environ.get("PINECONE_INDEX", "agentforge"))

    async def upsert(self, kb_id: str, records: list[dict]) -> int:
        try:
            self._index().upsert(
                vectors=[(r["id"], r["vector"], {"text": r["text"], **(r.get("metadata") or {})})
                         for r in records],
                namespace=kb_id,
            )
            return len(records)
        except Exception:
            return await NumpyStore().upsert(kb_id, records)

    async def query(self, kb_id: str, vector: list[float], k: int = 5) -> list[dict]:
        try:
            res = self._index().query(vector=vector, top_k=k, namespace=kb_id, include_metadata=True)
            return [
                {"text": m["metadata"].get("text", ""), "score": round(float(m["score"]), 4),
                 "metadata": {kk: vv for kk, vv in m["metadata"].items() if kk != "text"}}
                for m in res["matches"]
            ]
        except Exception:
            return await NumpyStore().query(kb_id, vector, k)


class WeaviateStore(VectorStoreAdapter):
    name = "weaviate"

    async def upsert(self, kb_id: str, records: list[dict]) -> int:
        try:
            import weaviate  # lazy

            client = weaviate.connect_to_local()
            try:
                coll = client.collections.get("AgentForgeChunk")
                with coll.batch.dynamic() as batch:
                    for r in records:
                        batch.add_object(
                            properties={"text": r["text"], "kb_id": kb_id},
                            vector=r["vector"],
                        )
                return len(records)
            finally:
                client.close()
        except Exception:
            return await NumpyStore().upsert(kb_id, records)

    async def query(self, kb_id: str, vector: list[float], k: int = 5) -> list[dict]:
        try:
            import weaviate  # lazy
            from weaviate.classes.query import Filter, MetadataQuery

            client = weaviate.connect_to_local()
            try:
                coll = client.collections.get("AgentForgeChunk")
                res = coll.query.near_vector(
                    near_vector=vector, limit=k,
                    filters=Filter.by_property("kb_id").equal(kb_id),
                    return_metadata=MetadataQuery(distance=True),
                )
                return [
                    {"text": o.properties.get("text", ""),
                     "score": round(1.0 - float(o.metadata.distance or 0.0), 4),
                     "metadata": {"kb_id": kb_id}}
                    for o in res.objects
                ]
            finally:
                client.close()
        except Exception:
            return await NumpyStore().query(kb_id, vector, k)


# --------------------------------------------------------------------------- #
_STORES: dict[str, Callable[[], VectorStoreAdapter]] = {
    "memory": NumpyStore,
    "pgvector": PgVectorStore,
    "chroma": ChromaStore,
    "qdrant": QdrantStore,
    "pinecone": PineconeStore,
    "weaviate": WeaviateStore,
}


def register_store(name: str, factory: Callable[[], VectorStoreAdapter]) -> None:
    """Plugin hook: register a custom vector store adapter."""
    _STORES[name] = factory


def get_store(name: str | None = None) -> VectorStoreAdapter:
    """Return the requested adapter (default pgvector) or NumpyStore fallback."""
    name = name or os.environ.get("VECTOR_STORE", "pgvector")
    factory = _STORES.get(name, NumpyStore)
    try:
        return factory()
    except Exception:
        return NumpyStore()
