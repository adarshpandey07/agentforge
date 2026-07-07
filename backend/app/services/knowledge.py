"""Knowledge service: document persistence + RAG ingestion via the AI engine."""
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models import Document, KnowledgeBase
from app.services import ai_bridge

logger = get_logger(__name__)


async def ingest_document(
    db: AsyncSession,
    *,
    kb: KnowledgeBase,
    name: str,
    source_type: str,
    content: bytes | str,
    metadata: dict[str, Any] | None = None,
) -> Document:
    """Create a documents row, run ingestion, and record chunk/status results."""
    meta = dict(metadata or {})
    document = Document(
        tenant_id=kb.tenant_id,
        kb_id=kb.id,
        name=name,
        source_type=source_type,
        status="processing",
        meta=meta,
    )
    db.add(document)
    await db.flush()

    try:
        result = await ai_bridge.ingest_source(
            kb_id=kb.id, source_type=source_type, content=content, metadata=meta
        )
        document.status = str(result.get("status", "indexed"))
        document.meta = {**meta, "chunks": result.get("chunks", 0), "stub": result.get("stub", False)}
    except Exception as exc:  # noqa: BLE001
        logger.warning("document ingestion failed", document_id=document.id, error=str(exc))
        document.status = "failed"
        document.meta = {**meta, "error": str(exc)}

    db.add(document)
    await db.commit()
    await db.refresh(document)
    return document
