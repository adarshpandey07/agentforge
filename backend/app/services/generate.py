"""Generate service: business prompt -> AgentSpec -> persisted project/agent/workflow/prompts."""
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Agent, Project, Prompt, PromptVersion, User, Workflow
from app.services import ai_bridge
from app.services.audit import record_audit


async def persist_spec(
    db: AsyncSession,
    *,
    user: User,
    spec: dict[str, Any],
    client_id: str | None = None,
    project_name: str | None = None,
) -> dict[str, Any]:
    """Persist an AgentSpec as project + agent + workflow + prompts (+versions)."""
    tenant_id = user.tenant_id
    name = project_name or spec.get("name", "Generated Agent")

    project = Project(
        tenant_id=tenant_id,
        client_id=client_id,
        name=name,
        description=spec.get("description", ""),
        status="active",
    )
    db.add(project)
    await db.flush()

    agent = Agent(
        tenant_id=tenant_id,
        project_id=project.id,
        name=spec.get("name", name),
        description=spec.get("description", ""),
        spec=spec,
        status="draft",
    )
    db.add(agent)
    await db.flush()

    workflow = Workflow(
        tenant_id=tenant_id,
        agent_id=agent.id,
        name=f"{agent.name} workflow",
        graph=spec.get("workflow", {"nodes": [], "edges": []}),
        version=1,
    )
    db.add(workflow)
    await db.flush()

    prompt_ids: list[str] = []
    for sub_agent in spec.get("agents", []):
        prompt = Prompt(
            tenant_id=tenant_id,
            project_id=project.id,
            name=f"{sub_agent.get('role', sub_agent.get('id', 'agent'))} system prompt",
            description=f"System prompt for sub-agent '{sub_agent.get('id', '')}'",
        )
        db.add(prompt)
        await db.flush()
        db.add(
            PromptVersion(
                tenant_id=tenant_id,
                prompt_id=prompt.id,
                content=sub_agent.get("system_prompt", ""),
                version=1,
                notes="Initial generated version",
            )
        )
        prompt_ids.append(prompt.id)

    await record_audit(
        db,
        user=user,
        action="generate",
        resource="agent",
        resource_id=agent.id,
        detail={"project_id": project.id, "workflow_id": workflow.id},
        commit=False,
    )
    await db.commit()
    return {
        "spec": spec,
        "project_id": project.id,
        "agent_id": agent.id,
        "workflow_id": workflow.id,
        "prompt_ids": prompt_ids,
    }


async def generate_and_persist(
    db: AsyncSession,
    *,
    user: User,
    prompt: str,
    business_type: str | None = None,
    client_id: str | None = None,
) -> dict[str, Any]:
    """Call the AI generator, then persist all resulting artifacts."""
    spec = await ai_bridge.generate_agent_spec(prompt, business_type)
    return await persist_spec(db, user=user, spec=spec, client_id=client_id)
