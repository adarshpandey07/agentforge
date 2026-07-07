"""POST /generate — business requirement to fully persisted AgentSpec."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, require_role
from app.models import User
from app.schemas.business import GenerateRequest, GenerateResponse
from app.services.generate import generate_and_persist

router = APIRouter(tags=["generate"])


@router.post("/generate", response_model=GenerateResponse, status_code=201)
async def generate(
    payload: GenerateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("member")),
) -> GenerateResponse:
    """Generate an AgentSpec from a natural-language business requirement and
    persist it as project + agent + workflow + prompts."""
    result = await generate_and_persist(
        db,
        user=user,
        prompt=payload.prompt,
        business_type=payload.business_type,
        client_id=payload.client_id,
    )
    return GenerateResponse(**result)
