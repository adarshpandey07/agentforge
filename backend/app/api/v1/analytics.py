"""GET /analytics/overview — tenant counts, cost and token totals."""
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models import (
    Agent,
    Client,
    Conversation,
    Deployment,
    LlmCall,
    Message,
    Project,
)
from app.models import User
from app.schemas.telemetry import AnalyticsOverview

router = APIRouter(prefix="/analytics", tags=["analytics"])


async def _count(db: AsyncSession, model, tenant_id: str) -> int:
    stmt = select(func.count()).select_from(model).where(model.tenant_id == tenant_id)
    return int((await db.execute(stmt)).scalar() or 0)


@router.get("/overview", response_model=AnalyticsOverview)
async def overview(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AnalyticsOverview:
    """Tenant-wide counts plus LLM cost and token usage totals."""
    tenant_id = user.tenant_id

    totals_stmt = select(
        func.coalesce(func.sum(LlmCall.cost), 0.0),
        func.coalesce(func.sum(LlmCall.prompt_tokens), 0),
        func.coalesce(func.sum(LlmCall.completion_tokens), 0),
        func.count(LlmCall.id),
    ).where(LlmCall.tenant_id == tenant_id)
    total_cost, prompt_tokens, completion_tokens, llm_calls = (
        (await db.execute(totals_stmt)).one()
    )

    return AnalyticsOverview(
        clients=await _count(db, Client, tenant_id),
        projects=await _count(db, Project, tenant_id),
        agents=await _count(db, Agent, tenant_id),
        conversations=await _count(db, Conversation, tenant_id),
        messages=await _count(db, Message, tenant_id),
        deployments=await _count(db, Deployment, tenant_id),
        llm_calls=int(llm_calls or 0),
        total_cost=float(total_cost or 0.0),
        prompt_tokens=int(prompt_tokens or 0),
        completion_tokens=int(completion_tokens or 0),
        tokens=int(prompt_tokens or 0) + int(completion_tokens or 0),
    )
