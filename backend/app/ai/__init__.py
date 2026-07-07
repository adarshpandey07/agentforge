"""AgentForge AI engine.

Public interface (per CONTRACT.md — BACKEND-CORE imports only these):

    from app.ai.generator import generate_agent_spec
    from app.ai.runtime import run_agent
    from app.ai.rag.ingest import ingest_source
    from app.ai.rag.retrieve import retrieve
    from app.ai.router.model_router import select_model
    from app.ai.templates import list_templates, get_template
    from app.ai.evaluate import simulate_agent

Every function degrades gracefully to deterministic stub responses
(marked ``"stub": true``) when no API keys are configured.
"""
from .evaluate import simulate_agent  # noqa: F401
from .generator import generate_agent_spec  # noqa: F401
from .rag.ingest import ingest_source  # noqa: F401
from .rag.retrieve import retrieve  # noqa: F401
from .router.model_router import select_model  # noqa: F401
from .runtime import run_agent  # noqa: F401
from .templates import get_template, list_templates  # noqa: F401

__all__ = [
    "generate_agent_spec", "run_agent", "ingest_source", "retrieve",
    "select_model", "list_templates", "get_template", "simulate_agent",
]
