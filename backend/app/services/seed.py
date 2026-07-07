"""Idempotent seeding of built-in marketplace data."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models import Template
from app.services import ai_bridge

logger = get_logger("agentforge.seed")


async def seed_builtin_templates(db: AsyncSession) -> int:
    """Insert the AI engine's built-in business templates as global public rows.

    Idempotent: only business types not already present as global (tenant_id IS NULL)
    templates are inserted, so tenant edits and re-runs are safe.
    """
    catalog = ai_bridge.list_templates()
    existing = set(
        (
            await db.execute(
                select(Template.business_type).where(Template.tenant_id.is_(None))
            )
        )
        .scalars()
        .all()
    )
    added = 0
    for entry in catalog:
        business_type = entry.get("business_type")
        if not business_type or business_type in existing:
            continue
        # catalog entries are summaries; fetch the full AgentSpec
        spec = ai_bridge.get_template(business_type)
        if not spec:
            logger.warning("builtin template missing full spec", business_type=business_type)
            continue
        db.add(
            Template(
                tenant_id=None,
                business_type=business_type,
                name=spec.get("name", business_type.replace("_", " ").title()),
                description=spec.get("description", ""),
                spec=spec,
                is_public=True,
            )
        )
        added += 1
    if added:
        await db.commit()
        logger.info("seeded builtin templates", added=added)
    return added
