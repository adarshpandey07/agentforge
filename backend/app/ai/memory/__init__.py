"""Memory subsystem: 5 memory kinds behind a common ABC + factory.

Every backend degrades to an in-process fallback so the platform works with
no Redis/Postgres/embedding service available.
"""
from __future__ import annotations

import json
import os
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Any, Optional


class MemoryBackend(ABC):
    """Common interface for all memory kinds."""

    kind: str = "base"

    def __init__(self, agent_id: str):
        self.agent_id = agent_id

    @abstractmethod
    async def append(self, key: str, item: dict) -> None:
        """Store one item under a key (e.g. session id / customer id)."""

    @abstractmethod
    async def get(self, key: str, limit: int = 20) -> list[dict]:
        """Fetch the most recent items for a key."""

    @abstractmethod
    async def clear(self, key: str) -> None:
        """Delete everything stored under a key."""


# --------------------------------------------------------------------------- #
class ShortTermMemory(MemoryBackend):
    """In-process rolling buffer of recent turns (per key)."""

    kind = "short_term"
    _buffers: dict[str, list[dict]] = defaultdict(list)

    def _bkey(self, key: str) -> str:
        return f"{self.agent_id}:{key}"

    async def append(self, key: str, item: dict) -> None:
        buf = self._buffers[self._bkey(key)]
        buf.append({**item, "ts": time.time()})
        del buf[:-50]  # keep last 50

    async def get(self, key: str, limit: int = 20) -> list[dict]:
        return self._buffers[self._bkey(key)][-limit:]

    async def clear(self, key: str) -> None:
        self._buffers.pop(self._bkey(key), None)


# --------------------------------------------------------------------------- #
class SessionMemory(MemoryBackend):
    """Redis-backed conversation history with an in-memory fallback."""

    kind = "session"
    _fallback: dict[str, list[dict]] = defaultdict(list)

    def _redis(self):
        url = os.environ.get("REDIS_URL")
        if not url:
            return None
        try:
            import redis.asyncio as aioredis  # lazy

            return aioredis.from_url(url, decode_responses=True)
        except Exception:
            return None

    def _rkey(self, key: str) -> str:
        return f"af:mem:session:{self.agent_id}:{key}"

    async def append(self, key: str, item: dict) -> None:
        r = self._redis()
        if r is not None:
            try:
                await r.rpush(self._rkey(key), json.dumps(item, default=str))
                await r.ltrim(self._rkey(key), -200, -1)
                await r.expire(self._rkey(key), 86_400)
                return
            except Exception:
                pass
        self._fallback[self._rkey(key)].append(item)

    async def get(self, key: str, limit: int = 20) -> list[dict]:
        r = self._redis()
        if r is not None:
            try:
                raw = await r.lrange(self._rkey(key), -limit, -1)
                return [json.loads(x) for x in raw]
            except Exception:
                pass
        return self._fallback[self._rkey(key)][-limit:]

    async def clear(self, key: str) -> None:
        r = self._redis()
        if r is not None:
            try:
                await r.delete(self._rkey(key))
                return
            except Exception:
                pass
        self._fallback.pop(self._rkey(key), None)


# --------------------------------------------------------------------------- #
class LongTermMemory(MemoryBackend):
    """Postgres-backed conversation summaries with in-memory fallback.

    Uses a raw asyncpg connection lazily; the table is created on demand.
    """

    kind = "long_term"
    _fallback: dict[str, list[dict]] = defaultdict(list)

    async def _conn(self):
        url = os.environ.get("DATABASE_URL", "")
        if not url:
            return None
        try:
            import asyncpg  # lazy

            dsn = url.replace("postgresql+asyncpg://", "postgresql://")
            conn = await asyncpg.connect(dsn, timeout=3)
            await conn.execute(
                """CREATE TABLE IF NOT EXISTS ai_long_term_memory (
                       id SERIAL PRIMARY KEY, agent_id TEXT, mem_key TEXT,
                       item JSONB, created_at TIMESTAMPTZ DEFAULT now())"""
            )
            return conn
        except Exception:
            return None

    async def append(self, key: str, item: dict) -> None:
        conn = await self._conn()
        if conn is not None:
            try:
                await conn.execute(
                    "INSERT INTO ai_long_term_memory (agent_id, mem_key, item) VALUES ($1,$2,$3)",
                    self.agent_id, key, json.dumps(item, default=str),
                )
                return
            except Exception:
                pass
            finally:
                try:
                    await conn.close()
                except Exception:
                    pass
        self._fallback[f"{self.agent_id}:{key}"].append(item)

    async def get(self, key: str, limit: int = 20) -> list[dict]:
        conn = await self._conn()
        if conn is not None:
            try:
                rows = await conn.fetch(
                    "SELECT item FROM ai_long_term_memory WHERE agent_id=$1 AND mem_key=$2 "
                    "ORDER BY id DESC LIMIT $3", self.agent_id, key, limit,
                )
                return [json.loads(r["item"]) for r in reversed(rows)]
            except Exception:
                pass
            finally:
                try:
                    await conn.close()
                except Exception:
                    pass
        return self._fallback[f"{self.agent_id}:{key}"][-limit:]

    async def clear(self, key: str) -> None:
        self._fallback.pop(f"{self.agent_id}:{key}", None)


# --------------------------------------------------------------------------- #
class VectorMemory(MemoryBackend):
    """Semantic memory: embeds items and retrieves by similarity.

    Falls back to deterministic hash-based embeddings when no key is set.
    """

    kind = "vector"
    _items: dict[str, list[dict]] = defaultdict(list)  # {ns: [{"text","vector","item"}]}

    def _ns(self, key: str) -> str:
        return f"{self.agent_id}:{key}"

    async def append(self, key: str, item: dict) -> None:
        from ..rag.embeddings import embed_texts

        text = item.get("text") or json.dumps(item, default=str)
        vecs = await embed_texts([text])
        self._items[self._ns(key)].append({"text": text, "vector": vecs[0], "item": item})

    async def get(self, key: str, limit: int = 20) -> list[dict]:
        return [e["item"] for e in self._items[self._ns(key)][-limit:]]

    async def search(self, key: str, query: str, k: int = 5) -> list[dict]:
        from ..rag.embeddings import cosine, embed_texts

        entries = self._items[self._ns(key)]
        if not entries:
            return []
        qv = (await embed_texts([query]))[0]
        scored = sorted(entries, key=lambda e: cosine(qv, e["vector"]), reverse=True)
        return [{"score": round(cosine(qv, e["vector"]), 4), **e["item"]} for e in scored[:k]]

    async def clear(self, key: str) -> None:
        self._items.pop(self._ns(key), None)


# --------------------------------------------------------------------------- #
class CustomerMemory(MemoryBackend):
    """Per-customer profile store (preferences, history highlights)."""

    kind = "customer"
    _profiles: dict[str, dict] = defaultdict(dict)

    def _pkey(self, key: str) -> str:
        return f"{self.agent_id}:{key}"

    async def append(self, key: str, item: dict) -> None:
        profile = self._profiles[self._pkey(key)]
        profile.setdefault("events", []).append({**item, "ts": time.time()})
        for k, v in item.items():
            if k not in ("events", "ts"):
                profile[k] = v

    async def get(self, key: str, limit: int = 20) -> list[dict]:
        profile = self._profiles.get(self._pkey(key), {})
        return [profile] if profile else []

    async def get_profile(self, key: str) -> dict:
        return self._profiles.get(self._pkey(key), {})

    async def clear(self, key: str) -> None:
        self._profiles.pop(self._pkey(key), None)


# --------------------------------------------------------------------------- #
_KINDS: dict[str, type[MemoryBackend]] = {
    "short_term": ShortTermMemory,
    "session": SessionMemory,
    "long_term": LongTermMemory,
    "vector": VectorMemory,
    "customer": CustomerMemory,
}


def get_memory(kind: str, agent_id: str) -> MemoryBackend:
    """Factory: return a memory backend instance for ``kind``."""
    cls = _KINDS.get(kind)
    if cls is None:
        raise ValueError(f"Unknown memory kind '{kind}'. Valid: {sorted(_KINDS)}")
    return cls(agent_id)


__all__ = [
    "MemoryBackend", "ShortTermMemory", "SessionMemory", "LongTermMemory",
    "VectorMemory", "CustomerMemory", "get_memory",
]
