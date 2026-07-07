"""Deployment service: generates deploy artifacts and records deployment rows."""
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError
from app.models import Agent, Deployment, User
from app.services.audit import record_audit

VALID_MODES = {"docker", "cloud", "vps", "local"}


def render_compose_artifact(agent: Agent) -> str:
    """Render a standalone docker-compose artifact serving one agent."""
    return f"""# AgentForge deployment artifact — agent: {agent.name} ({agent.id})
version: "3.9"
services:
  agent-runtime:
    image: agentforge/backend:latest
    environment:
      - AGENT_ID={agent.id}
      - DATABASE_URL=postgresql+asyncpg://agentforge:agentforge@postgres:5432/agentforge
      - REDIS_URL=redis://redis:6379/0
    ports:
      - "8080:8000"
    depends_on:
      - postgres
      - redis
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      - POSTGRES_DB=agentforge
      - POSTGRES_USER=agentforge
      - POSTGRES_PASSWORD=agentforge
  redis:
    image: redis:7-alpine
"""


async def create_deployment(
    db: AsyncSession, *, user: User, agent: Agent, mode: str
) -> Deployment:
    """Generate deploy artifacts for an agent and persist the deployment row."""
    if mode not in VALID_MODES:
        raise BadRequestError(f"Invalid deployment mode '{mode}'. Valid: {sorted(VALID_MODES)}")

    artifact = render_compose_artifact(agent)
    url = f"http://localhost:8000/api/v1/agents/{agent.id}/chat" if mode in {"docker", "local"} else ""
    deployment = Deployment(
        tenant_id=user.tenant_id,
        agent_id=agent.id,
        mode=mode,
        status="generated" if mode in {"docker", "local"} else "pending",
        url=url,
        artifact=artifact,
    )
    db.add(deployment)
    agent.status = "deployed"
    db.add(agent)
    await record_audit(
        db,
        user=user,
        action="create",
        resource="deployment",
        resource_id=None,
        detail={"agent_id": agent.id, "mode": mode},
        commit=False,
    )
    await db.commit()
    await db.refresh(deployment)
    return deployment
