"""Recursive text chunker with overlap."""
from __future__ import annotations

_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    """Split text recursively on natural boundaries with character overlap."""
    text = (text or "").strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    def split(t: str, seps: list[str]) -> list[str]:
        if len(t) <= chunk_size:
            return [t]
        if not seps:
            return [t[i:i + chunk_size] for i in range(0, len(t), chunk_size)]
        sep, rest = seps[0], seps[1:]
        parts = t.split(sep) if sep else list(t)
        pieces: list[str] = []
        for p in parts:
            if len(p) > chunk_size:
                pieces.extend(split(p, rest))
            elif p:
                pieces.append(p)
        # merge pieces up to chunk_size
        merged: list[str] = []
        cur = ""
        for p in pieces:
            candidate = (cur + sep + p) if cur else p
            if len(candidate) <= chunk_size:
                cur = candidate
            else:
                if cur:
                    merged.append(cur)
                cur = p
        if cur:
            merged.append(cur)
        return merged

    chunks = split(text, _SEPARATORS)
    if overlap <= 0 or len(chunks) < 2:
        return [c.strip() for c in chunks if c.strip()]
    out: list[str] = []
    for i, c in enumerate(chunks):
        prefix = chunks[i - 1][-overlap:] if i > 0 else ""
        out.append((prefix + c).strip())
    return [c for c in out if c]
