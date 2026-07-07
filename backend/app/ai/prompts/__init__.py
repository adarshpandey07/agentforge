"""Prompt template engine: {variable} substitution, metadata, optimize/test."""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Any


class _SafeDict(dict):
    def __missing__(self, key: str) -> str:  # leave unknown vars intact
        return "{" + key + "}"


@dataclass
class PromptTemplate:
    """A reusable prompt with ``{variable}`` placeholders and metadata."""

    template: str
    name: str = "unnamed"
    description: str = ""
    metadata: dict = field(default_factory=dict)

    @property
    def variables(self) -> list[str]:
        return sorted(set(re.findall(r"{(\w+)}", self.template)))

    def render(self, **variables: Any) -> str:
        return self.template.format_map(_SafeDict(**variables))

    def partial(self, **variables: Any) -> "PromptTemplate":
        return PromptTemplate(
            template=self.render(**variables),
            name=self.name,
            description=self.description,
            metadata=dict(self.metadata),
        )


_OPTIMIZE_INSTRUCTIONS = (
    "You are a prompt engineer. Rewrite the following system prompt to be "
    "clearer, more specific and more robust. Keep the intent, add structure "
    "(role, duties, constraints, tone, escalation), and return ONLY the "
    "improved prompt.\n\nPROMPT:\n{prompt}"
)


async def optimize_prompt(prompt: str) -> dict:
    """Improve a prompt via the routed LLM; deterministic stub without keys.

    Returns ``{"original", "optimized", "stub"}``.
    """
    from ..router.model_router import get_chat_model, select_model

    choice = select_model("prompt optimization", {"priority": "accuracy", "require_available": True})
    llm = get_chat_model(choice["provider"], choice["model"])
    if llm is not None:
        try:
            msg = await llm.ainvoke(_OPTIMIZE_INSTRUCTIONS.format(prompt=prompt))
            return {"original": prompt, "optimized": getattr(msg, "content", str(msg)), "stub": False}
        except Exception:
            pass

    # Deterministic heuristic improvement.
    improved = prompt.strip()
    additions = []
    low = improved.lower()
    if "you are" not in low:
        additions.append("You are a professional, helpful AI assistant.")
    if "tone" not in low:
        additions.append("Tone: warm, concise and professional. Never invent facts.")
    if "escalat" not in low:
        additions.append("If the request is outside your scope, say so and escalate to a human.")
    optimized = " ".join(additions + [improved]) if additions else improved
    return {"original": prompt, "optimized": optimized, "stub": True}


async def test_prompt(prompt: str, input: str) -> dict:  # noqa: A002 - contract name
    """Run a prompt against an input and return the model reply + telemetry."""
    from ..router.model_router import estimate_cost, get_chat_model, select_model

    choice = select_model("prompt test", {"priority": "cost", "require_available": True})
    llm = get_chat_model(choice["provider"], choice["model"])
    start = time.time()
    if llm is not None:
        try:
            msg = await llm.ainvoke([("system", prompt), ("user", input)])
            reply = getattr(msg, "content", str(msg))
            tokens = (len(prompt) + len(input) + len(reply)) // 4
            return {
                "reply": reply,
                "model": choice["model"],
                "latency_ms": int((time.time() - start) * 1000),
                "tokens": tokens,
                "cost": estimate_cost(choice["model"], tokens),
                "stub": False,
            }
        except Exception:
            pass
    reply = (
        f"[stub] With this system prompt the agent would answer '{input[:120]}' "
        f"following these instructions: {prompt[:200]}..."
    )
    return {
        "reply": reply,
        "model": choice["model"],
        "latency_ms": int((time.time() - start) * 1000),
        "tokens": (len(prompt) + len(input)) // 4,
        "cost": 0.0,
        "stub": True,
    }


__all__ = ["PromptTemplate", "optimize_prompt", "test_prompt"]
