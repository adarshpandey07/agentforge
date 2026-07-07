"""Model router: provider registry + model catalog + selection logic.

Pure-python at import time. LangChain chat-model classes are imported lazily
inside ``get_chat_model`` so this module never fails to import when third-party
dependencies are missing.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

# --------------------------------------------------------------------------- #
# Provider registry (plugin pattern)
# --------------------------------------------------------------------------- #


@dataclass
class Provider:
    """A registered LLM provider."""

    name: str
    env_key: str                       # env var holding the API key (or base URL for ollama)
    chat_class: str                    # dotted path to the LangChain chat class
    chat_kwargs: dict = field(default_factory=dict)
    key_optional: bool = False         # ollama needs no API key


PROVIDERS: dict[str, Provider] = {}


def register_provider(provider: Provider, models: Optional[list[dict]] = None) -> None:
    """Register a provider (and optionally its models). Extensibility hook."""
    PROVIDERS[provider.name] = provider
    if models:
        for m in models:
            m.setdefault("provider", provider.name)
            MODELS.append(m)


# --------------------------------------------------------------------------- #
# Model catalog
# --------------------------------------------------------------------------- #
# latency: 1=fast, 2=medium, 3=slow · quality: 1-5 · cost is USD per 1k tokens
MODELS: list[dict] = [
    {"provider": "openai",    "model": "gpt-4o",           "cost_per_1k": 0.0075, "latency": 2, "context": 128_000,   "quality": 5},
    {"provider": "openai",    "model": "gpt-4o-mini",      "cost_per_1k": 0.0004, "latency": 1, "context": 128_000,   "quality": 3},
    {"provider": "anthropic", "model": "claude-sonnet-5",  "cost_per_1k": 0.0090, "latency": 2, "context": 200_000,   "quality": 5},
    {"provider": "anthropic", "model": "claude-haiku-4-5", "cost_per_1k": 0.0020, "latency": 1, "context": 200_000,   "quality": 4},
    {"provider": "google",    "model": "gemini-2.0-flash", "cost_per_1k": 0.0003, "latency": 1, "context": 1_000_000, "quality": 4},
    {"provider": "deepseek",  "model": "deepseek-chat",    "cost_per_1k": 0.0006, "latency": 2, "context": 64_000,    "quality": 4},
    {"provider": "ollama",    "model": "llama3",           "cost_per_1k": 0.0,    "latency": 3, "context": 8_000,     "quality": 2},
]

register_provider(Provider("openai", "OPENAI_API_KEY", "langchain_openai.ChatOpenAI"))
register_provider(Provider("anthropic", "ANTHROPIC_API_KEY", "langchain_anthropic.ChatAnthropic"))
register_provider(Provider("google", "GOOGLE_API_KEY", "langchain_google_genai.ChatGoogleGenerativeAI"))
register_provider(Provider(
    "deepseek", "DEEPSEEK_API_KEY", "langchain_openai.ChatOpenAI",
    chat_kwargs={"base_url": "https://api.deepseek.com/v1"},
))
register_provider(Provider("ollama", "OLLAMA_BASE_URL", "langchain_community.chat_models.ChatOllama", key_optional=True))


def provider_available(name: str) -> bool:
    """True when the provider has credentials configured in the environment."""
    p = PROVIDERS.get(name)
    if p is None:
        return False
    return bool(os.environ.get(p.env_key))


# --------------------------------------------------------------------------- #
# Selection
# --------------------------------------------------------------------------- #
_PRIORITY_WEIGHTS: dict[str, dict[str, float]] = {
    # score = quality*wq - cost_norm*wc - latency*wl
    "cost":     {"quality": 1.0, "cost": 6.0, "latency": 0.5},
    "latency":  {"quality": 1.0, "cost": 0.5, "latency": 4.0},
    "accuracy": {"quality": 4.0, "cost": 0.2, "latency": 0.2},
    "balanced": {"quality": 2.0, "cost": 2.0, "latency": 1.0},
}


def _score(m: dict, weights: dict[str, float]) -> float:
    cost_norm = min(m["cost_per_1k"] / 0.01, 1.0)  # normalise against 1c/1k
    return (
        m["quality"] * weights["quality"]
        - cost_norm * weights["cost"]
        - m["latency"] * weights["latency"]
    )


def select_model(task: str, constraints: dict | None = None) -> dict:
    """Pick the best model for ``task`` under ``constraints``.

    constraints keys (all optional): ``priority`` (cost|latency|accuracy|balanced),
    ``max_cost_per_1k_tokens``, ``min_context``, ``provider`` (force),
    ``require_available`` (only providers with configured keys).
    Returns ``{"provider", "model", "reason", "est_cost_per_1k"}``.
    """
    c = dict(constraints or {})
    priority = c.get("priority", "balanced")
    weights = _PRIORITY_WEIGHTS.get(priority, _PRIORITY_WEIGHTS["balanced"])

    candidates = list(MODELS)
    if c.get("provider"):
        candidates = [m for m in candidates if m["provider"] == c["provider"]]
    if c.get("max_cost_per_1k_tokens") is not None:
        candidates = [m for m in candidates if m["cost_per_1k"] <= c["max_cost_per_1k_tokens"]]
    if c.get("min_context") is not None:
        candidates = [m for m in candidates if m["context"] >= c["min_context"]]
    if c.get("require_available"):
        avail = [m for m in candidates if provider_available(m["provider"])]
        if avail:
            candidates = avail
    if not candidates:  # constraints too tight — fall back to full catalog
        candidates = list(MODELS)

    # Long or complex tasks nudge toward higher quality.
    task_l = (task or "").lower()
    complex_task = any(w in task_l for w in ("reason", "analy", "legal", "code", "plan", "complex", "generat"))

    def rank(m: dict) -> float:
        s = _score(m, weights)
        if complex_task:
            s += m["quality"] * 0.8
        return s

    best = max(candidates, key=rank)
    return {
        "provider": best["provider"],
        "model": best["model"],
        "reason": (
            f"priority={priority}; quality={best['quality']}/5, "
            f"latency_class={best['latency']}, context={best['context']}, "
            f"cost=${best['cost_per_1k']}/1k"
            + ("; task looks complex → quality boosted" if complex_task else "")
        ),
        "est_cost_per_1k": best["cost_per_1k"],
    }


def get_chat_model(provider: str, model: str, temperature: float = 0.3) -> Any:
    """Instantiate the LangChain chat model for provider/model.

    Lazy-imports the provider class. Returns ``None`` when the dependency or
    the credential is missing — callers must handle the stub path.
    """
    p = PROVIDERS.get(provider)
    if p is None:
        return None
    if not p.key_optional and not os.environ.get(p.env_key):
        return None
    module_path, _, cls_name = p.chat_class.rpartition(".")
    try:
        import importlib

        cls = getattr(importlib.import_module(module_path), cls_name)
        kwargs: dict[str, Any] = {"model": model, "temperature": temperature, **p.chat_kwargs}
        if provider == "deepseek":
            kwargs["api_key"] = os.environ.get(p.env_key)
        if provider == "ollama":
            kwargs["base_url"] = os.environ.get(p.env_key, "http://localhost:11434")
        return cls(**kwargs)
    except Exception:
        return None


def estimate_cost(model: str, tokens: int) -> float:
    """Cost estimate for a token count against the catalog."""
    for m in MODELS:
        if m["model"] == model:
            return round(m["cost_per_1k"] * tokens / 1000.0, 6)
    return 0.0
