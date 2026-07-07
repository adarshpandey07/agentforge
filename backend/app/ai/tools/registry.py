"""Tool plugin registry.

``ToolPlugin`` is the ABC every tool implements. ``@register_tool`` registers
a plugin class or instance. ``get_tools_for_spec`` returns LangChain-compatible
tools when langchain is installed, otherwise the raw plugins (the runtime stub
path calls ``plugin.execute`` directly).
"""
from __future__ import annotations

import inspect
import os
from abc import ABC, abstractmethod
from typing import Any, Callable, Optional


class ToolPlugin(ABC):
    """A pluggable tool: metadata + async execute."""

    name: str = "tool"
    description: str = ""
    schema: dict = {"type": "object", "properties": {}, "required": []}
    required_env: tuple[str, ...] = ()   # creds needed for real execution

    def configured(self) -> bool:
        return all(os.environ.get(k) for k in self.required_env)

    @abstractmethod
    async def execute(self, **kwargs: Any) -> dict:
        """Run the tool. Must return a JSON-serialisable dict.

        Implementations return ``{"stub": True, ...}`` when creds are missing.
        """


TOOLS: dict[str, ToolPlugin] = {}


def register_tool(obj: Any = None) -> Any:
    """Decorator/function to register a ToolPlugin class or instance."""

    def _register(o: Any) -> Any:
        instance = o() if inspect.isclass(o) else o
        TOOLS[instance.name] = instance
        return o

    return _register(obj) if obj is not None else _register


def get_tool(name: str) -> Optional[ToolPlugin]:
    return TOOLS.get(name)


def list_tools() -> list[dict]:
    return [
        {"name": t.name, "description": t.description, "schema": t.schema,
         "configured": t.configured()}
        for t in TOOLS.values()
    ]


def _to_langchain_tool(plugin: ToolPlugin, config: dict | None = None) -> Any:
    """Wrap a plugin as a LangChain StructuredTool (lazy import)."""
    try:
        from langchain_core.tools import StructuredTool  # lazy
    except Exception:
        return plugin

    cfg = config or {}

    async def _run(**kwargs: Any) -> dict:
        return await plugin.execute(**{**cfg, **kwargs})

    return StructuredTool.from_function(
        coroutine=_run, name=plugin.name, description=plugin.description or plugin.name,
    )


def get_tools_for_spec(spec: dict) -> list[Any]:
    """Resolve every tool referenced by an AgentSpec into runnable tools."""
    from . import builtins as _builtins  # noqa: F401  ensure builtins registered

    wanted: dict[str, dict] = {}
    for t in spec.get("tools", []) or []:
        wanted[t.get("name", "")] = t.get("config", {}) or {}
    for a in spec.get("agents", []) or []:
        for name in a.get("tools", []) or []:
            wanted.setdefault(name, {})

    out: list[Any] = []
    for name, cfg in wanted.items():
        plugin = TOOLS.get(name)
        if plugin is None:
            continue
        out.append(_to_langchain_tool(plugin, cfg))
    return out
