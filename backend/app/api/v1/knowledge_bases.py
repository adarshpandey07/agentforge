"""Knowledge bases CRUD + document upload / URL ingestion."""
from typing import Any

from fastapi import Depends, File, Form, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.crud_factory import build_crud_router
from app.core.deps import get_current_user, get_db, require_role
from app.core.exceptions import BadRequestError
from app.models import Document, KnowledgeBase, User
from app.schemas.content import (
    DocumentRead,
    KnowledgeBaseCreate,
    KnowledgeBaseRead,
    KnowledgeBaseUpdate,
)
from app.services.audit import record_audit
from app.services.knowledge import ingest_document

router, service = build_crud_router(
    prefix="/knowledge-bases",
    tag="knowledge-bases",
    resource="knowledge_base",
    model=KnowledgeBase,
    read_schema=KnowledgeBaseRead,
    create_schema=KnowledgeBaseCreate,
    update_schema=KnowledgeBaseUpdate,
)


@router.get("/{kb_id}/documents", response_model=list[DocumentRead])
async def list_documents(
    kb_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Any:
    """List documents in a knowledge base."""
    kb = await service.get(db, tenant_id=user.tenant_id, item_id=kb_id)
    stmt = (
        select(Document)
        .where(Document.tenant_id == user.tenant_id, Document.kb_id == kb.id)
        .order_by(Document.created_at.desc())
    )
    return list((await db.execute(stmt)).scalars().all())


@router.post("/{kb_id}/documents", response_model=DocumentRead, status_code=201)
async def add_document(
    kb_id: str,
    file: UploadFile | None = File(default=None),
    url: str | None = Form(default=None),
    text: str | None = Form(default=None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("member")),
) -> Any:
    """Ingest a document from a file upload, a URL, or raw text (multipart form)."""
    kb = await service.get(db, tenant_id=user.tenant_id, item_id=kb_id)

    if file is not None:
        content: bytes | str = await file.read()
        name = file.filename or "upload"
        source_type = "file"
        metadata = {"filename": name, "content_type": file.content_type}
    elif url:
        content = url
        name = url
        source_type = "url"
        metadata = {"url": url}
    elif text:
        content = text
        name = "inline-text"
        source_type = "text"
        metadata = {}
    else:
        raise BadRequestError("Provide one of: file upload, url, or text")

    document = await ingest_document(
        db, kb=kb, name=name, source_type=source_type, content=content, metadata=metadata
    )
    await record_audit(
        db, user=user, action="create", resource="document",
        resource_id=document.id, detail={"kb_id": kb.id, "source_type": source_type},
    )
    return document
