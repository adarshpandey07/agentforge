"""Guarded imports of the AI public interface (CONTRACT.md).

The AI engine (app/ai/) is built by a separate agent. Every import is wrapped
so the backend imports and runs even when the ai package is absent or broken;
in that case deterministic stubs (marked "stub": true) are used.
"""
import uuid
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


def _stub_spec(prompt: str, business_type: str | None = None) -> dict[str, Any]:
    name = f"{(business_type or 'business').replace('_', ' ').title()} Assistant"
    return {
        "version": 1,
        "name": name,
        "business_type": business_type or "generic",
        "description": f"Auto-generated agent for: {prompt[:200]}",
        "model_policy": {
            "preferred": "auto",
            "constraints": {"max_cost_per_1k_tokens": 0.01, "min_context": 32000, "priority": "balanced"},
        },
        "agents": [
            {
                "id": "receptionist",
                "role": "Receptionist",
                "system_prompt": f"You are a helpful receptionist for a {business_type or 'business'}. {prompt}",
                "tools": ["faq_rag"],
                "memory": ["session", "customer"],
                "model": "auto",
            }
        ],
        "supervisor": {"enabled": False, "routing_prompt": ""},
        "workflow": {
            "nodes": [
                {"id": "input", "type": "input", "ref": None, "position": {"x": 0, "y": 0}},
                {"id": "n1", "type": "agent", "ref": "receptionist", "position": {"x": 250, "y": 0}},
                {"id": "output", "type": "output", "ref": None, "position": {"x": 500, "y": 0}},
            ],
            "edges": [
                {"source": "input", "target": "n1", "condition": None},
                {"source": "n1", "target": "output", "condition": None},
            ],
        },
        "tools": [{"name": "faq_rag", "type": "builtin", "provider": "rag", "config": {}}],
        "rag": {"enabled": True, "vector_store": "pgvector", "embedding_model": "text-embedding-3-small", "sources": []},
        "memory": {"short_term": True, "long_term": True, "vector": True, "session": True, "customer": True},
        "integrations": [],
        "deployment": {"mode": "docker", "channels": ["web"]},
        "stub": True,
    }


try:  # pragma: no cover - depends on AI engine availability
    from app.ai.generator import generate_agent_spec  # type: ignore
except Exception:  # noqa: BLE001
    logger.warning("app.ai.generator unavailable; using stub generate_agent_spec")

    async def generate_agent_spec(prompt: str, business_type: str | None = None) -> dict:
        return _stub_spec(prompt, business_type)


try:  # pragma: no cover
    from app.ai.runtime import run_agent  # type: ignore
except Exception:  # noqa: BLE001
    logger.warning("app.ai.runtime unavailable; using stub run_agent")

    async def run_agent(
        spec: dict, message: str, session_id: str, context: dict | None = None
    ) -> dict:
        name = spec.get("name", "Agent")
        return {
            "reply": f"[stub] {name} received: {message}",
            "llm_calls": [
                {
                    "model": "stub-model",
                    "provider": "stub",
                    "prompt_tokens": max(1, len(message) // 4),
                    "completion_tokens": 16,
                    "cost": 0.0,
                    "latency_ms": 1,
                }
            ],
            "tool_calls": [],
            "tokens": {"prompt": max(1, len(message) // 4), "completion": 16},
            "cost": 0.0,
            "stub": True,
        }


try:  # pragma: no cover
    from app.ai.rag.ingest import ingest_source  # type: ignore
except Exception:  # noqa: BLE001
    logger.warning("app.ai.rag.ingest unavailable; using stub ingest_source")

    async def ingest_source(
        kb_id: str, source_type: str, content: bytes | str, metadata: dict
    ) -> dict:
        size = len(content) if content else 0
        return {"chunks": max(1, size // 1000), "status": "indexed", "stub": True}


try:  # pragma: no cover
    from app.ai.rag.retrieve import retrieve  # type: ignore
except Exception:  # noqa: BLE001

    async def retrieve(kb_id: str, query: str, k: int = 5) -> list[dict]:
        return [{"content": f"[stub] no vector store; query={query}", "score": 0.0, "stub": True}]


try:  # pragma: no cover
    from app.ai.router.model_router import select_model  # type: ignore
except Exception:  # noqa: BLE001

    def select_model(task: str, constraints: dict | None = None) -> dict:
        return {
            "provider": "stub",
            "model": "stub-model",
            "reason": "AI router unavailable; stub selection",
            "est_cost_per_1k": 0.0,
            "stub": True,
        }


try:  # pragma: no cover
    from app.ai.templates import get_template, list_templates  # type: ignore
except Exception:  # noqa: BLE001

    def list_templates() -> list[dict]:
        return [_stub_spec("Template catalog unavailable", "bakery")]

    def get_template(business_type: str) -> dict:
        return _stub_spec(f"Template for {business_type}", business_type)


try:  # pragma: no cover
    from app.ai.evaluate import simulate_agent  # type: ignore
except Exception:  # noqa: BLE001

    async def simulate_agent(spec: dict, scenario: str, turns: int = 5) -> dict:
        return {
            "id": str(uuid.uuid4()),
            "scenario": scenario,
            "turns": turns,
            "transcript": [{"role": "system", "content": "[stub] simulation unavailable"}],
            "score": None,
            "passed": None,
            "stub": True,
        }


__all__ = [
    "generate_agent_spec",
    "run_agent",
    "ingest_source",
    "retrieve",
    "select_model",
    "list_templates",
    "get_template",
    "simulate_agent",
]
