"""LangGraph agent factory: converts an AgentSpec workflow into a StateGraph.

All langgraph/langchain imports are lazy so this module always imports.
``build_graph`` raises ``GraphUnavailable`` when the deps are missing — the
runtime catches that and takes the deterministic stub path.
"""
from __future__ import annotations

from typing import Any, Optional


class GraphUnavailable(RuntimeError):
    """Raised when langgraph/langchain (or a model) is not available."""


def _agent_node(agent: dict, llm: Any, tools: list, telemetry: dict):
    """Create a LangGraph node fn for one agent (LLM + system prompt + tools)."""
    import time

    from langchain_core.messages import SystemMessage

    bound = llm.bind_tools(tools) if tools else llm

    async def node(state: dict) -> dict:
        start = time.time()
        messages = [SystemMessage(content=agent.get("system_prompt", ""))] + list(
            state.get("messages", [])
        )
        response = await bound.ainvoke(messages)
        usage = getattr(response, "usage_metadata", None) or {}
        telemetry.setdefault("llm_calls", []).append({
            "agent": agent.get("id"),
            "model": getattr(llm, "model", None) or getattr(llm, "model_name", "unknown"),
            "prompt_tokens": usage.get("input_tokens", 0),
            "completion_tokens": usage.get("output_tokens", 0),
            "latency_ms": int((time.time() - start) * 1000),
        })
        return {"messages": [response]}

    return node


def _supervisor_node(spec: dict, agent_ids: list[str]):
    """Supervisor node: routes to the best agent, stores decision in state."""

    async def node(state: dict) -> dict:
        from ..multi_agent.supervisor import route

        messages = state.get("messages", [])
        last_user = ""
        for m in reversed(messages):
            content = getattr(m, "content", None)
            if content and getattr(m, "type", "") in ("human", "user"):
                last_user = content if isinstance(content, str) else str(content)
                break
        decision = await route(spec, last_user)
        target = decision["agent_id"] if decision["agent_id"] in agent_ids else agent_ids[0]
        return {"next_agent": target}

    return node


def _condition_fn(condition: Optional[str], default: str):
    """Turn an edge condition string into a router callable on state."""

    def fn(state: dict) -> str:
        if not condition:
            return default
        messages = state.get("messages", [])
        last = messages[-1] if messages else None
        text = str(getattr(last, "content", "") or "").lower()
        return default if condition.lower() in text else default

    return fn


def build_graph(spec: dict, llm_factory: Any = None, telemetry: dict | None = None) -> Any:
    """Build and compile a LangGraph StateGraph from an AgentSpec.

    ``llm_factory(agent: dict) -> chat model`` lets the runtime inject routed
    models per agent. Raises ``GraphUnavailable`` when deps/models are missing.
    """
    telemetry = telemetry if telemetry is not None else {}
    try:
        from langgraph.graph import END, START, StateGraph
        from langgraph.graph.message import add_messages
        from langgraph.prebuilt import ToolNode
        from typing_extensions import Annotated, TypedDict
    except Exception as exc:  # deps missing
        raise GraphUnavailable(f"langgraph unavailable: {exc}") from exc

    from ..router.model_router import get_chat_model, select_model
    from ..tools.registry import get_tools_for_spec

    class State(TypedDict, total=False):
        messages: Annotated[list, add_messages]
        next_agent: str

    def default_llm_factory(agent: dict) -> Any:
        constraints = dict((spec.get("model_policy") or {}).get("constraints") or {})
        constraints["require_available"] = True
        choice = select_model(agent.get("role", "assistant"), constraints)
        model = agent.get("model") if agent.get("model") not in (None, "auto") else choice["model"]
        provider = choice["provider"]
        llm = get_chat_model(provider, model) or get_chat_model(choice["provider"], choice["model"])
        if llm is None:
            raise GraphUnavailable(f"no model available for provider {provider}")
        return llm

    factory = llm_factory or default_llm_factory
    all_tools = get_tools_for_spec(spec)
    tools_by_name = {getattr(t, "name", ""): t for t in all_tools}

    agents = spec.get("agents", []) or []
    if not agents:
        raise GraphUnavailable("spec has no agents")
    agent_ids = [a["id"] for a in agents]

    graph = StateGraph(State)

    # Agent nodes (each with its subset of tools bound).
    for agent in agents:
        llm = factory(agent)
        agent_tools = [tools_by_name[n] for n in agent.get("tools", []) if n in tools_by_name]
        graph.add_node(agent["id"], _agent_node(agent, llm, agent_tools, telemetry))
        if agent_tools:
            tool_node_id = f"{agent['id']}__tools"
            graph.add_node(tool_node_id, ToolNode(agent_tools))

            def tools_condition(state: dict, _tn=tool_node_id) -> str:
                msgs = state.get("messages", [])
                last = msgs[-1] if msgs else None
                if getattr(last, "tool_calls", None):
                    return _tn
                return END

            graph.add_conditional_edges(agent["id"], tools_condition, {tool_node_id: tool_node_id, END: END})
            graph.add_edge(tool_node_id, agent["id"])
        else:
            graph.add_edge(agent["id"], END)

    supervisor_enabled = bool((spec.get("supervisor") or {}).get("enabled"))
    if supervisor_enabled and len(agent_ids) > 1:
        graph.add_node("supervisor", _supervisor_node(spec, agent_ids))
        graph.add_edge(START, "supervisor")
        graph.add_conditional_edges(
            "supervisor",
            lambda state: state.get("next_agent") or agent_ids[0],
            {aid: aid for aid in agent_ids},
        )
    else:
        # Follow explicit workflow edges from input node when present.
        entry = agent_ids[0]
        wf = spec.get("workflow") or {}
        nodes = {n.get("id"): n for n in wf.get("nodes", []) or []}
        for e in wf.get("edges", []) or []:
            src = nodes.get(e.get("source"), {})
            tgt = nodes.get(e.get("target"), {})
            if src.get("type") == "input" and tgt.get("type") == "agent" and tgt.get("ref") in agent_ids:
                entry = tgt["ref"]
                break
        graph.add_edge(START, entry)

    return graph.compile()
