"""Background tasks: async document ingestion and agent simulation."""
import asyncio
from typing import Any

from app.core.logging import get_logger
from app.workers.celery_app import celery_app

logger = get_logger("agentforge.workers")


async def _ingest_document_async(document_id: str, content_text: str) -> dict[str, Any]:
    from sqlalchemy import select

    from app.db.session import async_session_factory
    from app.models import Document, KnowledgeBase
    from app.services import ai_bridge

    async with async_session_factory() as db:
        document = (
            await db.execute(select(Document).where(Document.id == document_id))
        ).scalars().first()
        if document is None:
            return {"status": "not_found", "document_id": document_id}
        kb = await db.get(KnowledgeBase, document.kb_id)
        try:
            result = await ai_bridge.ingest_source(
                kb_id=kb.id if kb else document.kb_id,
                source_type=document.source_type,
                content=content_text,
                metadata=document.meta or {},
            )
            document.status = str(result.get("status", "indexed"))
            document.meta = {**(document.meta or {}), "chunks": result.get("chunks", 0)}
        except Exception as exc:  # noqa: BLE001
            document.status = "failed"
            document.meta = {**(document.meta or {}), "error": str(exc)}
        db.add(document)
        await db.commit()
        return {"status": document.status, "document_id": document_id}


async def _simulate_agent_async(agent_id: str, scenario: str, turns: int) -> dict[str, Any]:
    from sqlalchemy import select

    from app.db.session import async_session_factory
    from app.models import Agent
    from app.services import ai_bridge

    async with async_session_factory() as db:
        agent = (
            await db.execute(select(Agent).where(Agent.id == agent_id))
        ).scalars().first()
        if agent is None:
            return {"status": "not_found", "agent_id": agent_id}
        report = await ai_bridge.simulate_agent(agent.spec or {}, scenario, turns)
        return {"status": "completed", "agent_id": agent_id, "report": report}


@celery_app.task(name="agentforge.ingest_document")
def ingest_document_task(document_id: str, content_text: str) -> dict[str, Any]:
    """Ingest a document into its knowledge base's vector store (async under the hood)."""
    logger.info("ingest task started", document_id=document_id)
    return asyncio.run(_ingest_document_async(document_id, content_text))


@celery_app.task(name="agentforge.simulate_agent")
def simulate_agent_task(agent_id: str, scenario: str, turns: int = 5) -> dict[str, Any]:
    """Run an automated evaluation scenario for an agent in the background."""
    logger.info("simulation task started", agent_id=agent_id)
    return asyncio.run(_simulate_agent_async(agent_id, scenario, turns))
