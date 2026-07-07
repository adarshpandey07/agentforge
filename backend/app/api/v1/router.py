"""Aggregate v1 API router."""
from fastapi import APIRouter

from app.api.v1 import (
    agents,
    analytics,
    api_keys,
    auth,
    clients,
    deployments,
    generate,
    integrations,
    knowledge_bases,
    logs,
    projects,
    prompts,
    templates,
    tools,
    workflows,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(clients.router)
api_router.include_router(projects.router)
api_router.include_router(agents.router)
api_router.include_router(workflows.router)
api_router.include_router(prompts.router)
api_router.include_router(knowledge_bases.router)
api_router.include_router(tools.router)
api_router.include_router(integrations.router)
api_router.include_router(templates.router)
api_router.include_router(deployments.router)
api_router.include_router(api_keys.router)
api_router.include_router(generate.router)
api_router.include_router(analytics.router)
api_router.include_router(logs.router)
