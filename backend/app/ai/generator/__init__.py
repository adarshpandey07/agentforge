"""AgentSpec generator: prompt (+ optional business_type) → complete AgentSpec.

Strategy:
1. business_type matches a shipped template → load + customize with the prompt.
2. LLM available via the router → generate JSON, validate, auto-fix.
3. No key → heuristic: keyword-match a template from the prompt, else a
   generic multi-agent spec built from role presets.
Always returns a COMPLETE, valid AgentSpec dict (validated by validate_spec).
"""
from __future__ import annotations

import copy
import json
import re
from typing import Optional

from ..multi_agent.teams import build_role
from ..router.model_router import get_chat_model, select_model

_BUSINESS_KEYWORDS: dict[str, tuple[str, ...]] = {
    "bakery": ("bakery", "baker", "cake", "pastry", "bread", "cupcake"),
    "barber": ("barber", "barbershop", "haircut for men", "fade", "beard"),
    "salon": ("salon", "hair", "spa", "beauty", "nails", "manicure"),
    "restaurant": ("restaurant", "cafe", "diner", "bistro", "food", "menu", "table"),
    "gym": ("gym", "fitness", "workout", "trainer", "crossfit", "yoga studio"),
    "dentist": ("dentist", "dental", "teeth", "orthodont"),
    "clinic": ("clinic", "doctor", "medical", "physician", "health center"),
    "lawyer": ("lawyer", "law firm", "attorney", "legal"),
    "real_estate": ("real estate", "realtor", "property", "listing", "broker"),
    "car_dealer": ("car dealer", "dealership", "auto", "vehicle", "test drive"),
    "travel_agency": ("travel", "tour", "trip", "itinerary", "vacation"),
    "hotel": ("hotel", "resort", "guest house", "bnb", "room booking"),
    "retail": ("retail", "shop", "store", "boutique"),
    "ecommerce": ("ecommerce", "e-commerce", "online store", "shopify store", "web shop"),
    "coaching_institute": ("coaching", "institute", "tuition", "academy", "classes",
                           "exam prep", "students"),
}


class SpecValidationError(ValueError):
    """Raised when a spec is invalid beyond repair."""


def _grid_position(i: int) -> dict:
    return {"x": 120 + (i % 3) * 280, "y": 80 + (i // 3) * 180}


def _default_workflow(agents: list[dict]) -> dict:
    """Synthesize a supervisor-centric workflow with laid-out positions."""
    nodes = [{"id": "input", "type": "input", "ref": None, "position": {"x": 40, "y": 220}},
             {"id": "supervisor", "type": "condition", "ref": "supervisor",
              "position": {"x": 300, "y": 220}}]
    edges = [{"source": "input", "target": "supervisor", "condition": None}]
    for i, a in enumerate(agents):
        nid = f"agent_{a['id']}"
        nodes.append({"id": nid, "type": "agent", "ref": a["id"],
                      "position": {"x": 580, "y": 80 + i * 160}})
        edges.append({"source": "supervisor", "target": nid,
                      "condition": f"route == '{a['id']}'"})
        edges.append({"source": nid, "target": "output", "condition": None})
    nodes.append({"id": "output", "type": "output", "ref": None,
                  "position": {"x": 880, "y": 220}})
    return {"nodes": nodes, "edges": edges}


def validate_spec(spec: dict, autofix: bool = True) -> dict:
    """Validate an AgentSpec against the contract schema.

    With ``autofix=True`` (default) missing fields are repaired in a copy and
    the fixed spec is returned. Without autofix, raises SpecValidationError
    listing every problem.
    """
    errors: list[str] = []
    if not isinstance(spec, dict):
        raise SpecValidationError("spec must be a dict")
    s = copy.deepcopy(spec)

    if not s.get("name"):
        errors.append("missing 'name'")
        s["name"] = "Unnamed Agent"
    s.setdefault("version", 1)
    s.setdefault("business_type", "generic")
    s.setdefault("description", f"AI agent team for {s['name']}")
    mp = s.setdefault("model_policy", {})
    mp.setdefault("preferred", "auto")
    mp.setdefault("constraints", {"max_cost_per_1k_tokens": 0.01,
                                  "min_context": 32000, "priority": "balanced"})

    agents = s.get("agents")
    if not agents or not isinstance(agents, list):
        errors.append("missing 'agents' list")
        s["agents"] = [build_role("receptionist", s["name"], s["business_type"])]
        agents = s["agents"]
    seen_ids: set[str] = set()
    for i, a in enumerate(agents):
        if not a.get("id"):
            errors.append(f"agents[{i}] missing 'id'")
            a["id"] = f"agent_{i}"
        if a["id"] in seen_ids:
            errors.append(f"duplicate agent id '{a['id']}'")
            a["id"] = f"{a['id']}_{i}"
        seen_ids.add(a["id"])
        a.setdefault("role", a["id"].replace("_", " ").title())
        if not a.get("system_prompt"):
            errors.append(f"agents[{i}] missing 'system_prompt'")
            a["system_prompt"] = (f"You are the {a['role']} for {s['name']}. Help "
                                  "customers accurately, concisely and politely.")
        a.setdefault("tools", [])
        a.setdefault("memory", ["session"])
        a.setdefault("model", "auto")

    sup = s.setdefault("supervisor", {})
    sup.setdefault("enabled", len(agents) > 1)
    if sup.get("enabled") and not sup.get("routing_prompt"):
        from ..multi_agent.supervisor import build_routing_prompt

        sup["routing_prompt"] = build_routing_prompt(s)

    wf = s.get("workflow")
    if not wf or not wf.get("nodes"):
        errors.append("missing 'workflow.nodes' — synthesized")
        s["workflow"] = _default_workflow(agents)
    else:
        for i, n in enumerate(wf.get("nodes", [])):
            n.setdefault("id", f"n{i}")
            n.setdefault("type", "agent")
            n.setdefault("ref", None)
            if not isinstance(n.get("position"), dict) or "x" not in (n.get("position") or {}):
                errors.append(f"workflow.nodes[{i}] missing position — auto-laid-out")
                n["position"] = _grid_position(i)
        wf.setdefault("edges", [])
        for e in wf["edges"]:
            e.setdefault("condition", None)

    # tools list: ensure every referenced tool has an entry
    tool_entries = {t.get("name") for t in s.get("tools", []) or []}
    s.setdefault("tools", [])
    for a in agents:
        for tn in a.get("tools", []):
            if tn not in tool_entries:
                s["tools"].append({"name": tn, "type": "builtin", "provider": tn, "config": {}})
                tool_entries.add(tn)

    rag = s.setdefault("rag", {})
    rag.setdefault("enabled", True)
    rag.setdefault("vector_store", "pgvector")
    rag.setdefault("embedding_model", "text-embedding-3-small")
    rag.setdefault("sources", [])

    mem = s.setdefault("memory", {})
    for k in ("short_term", "long_term", "vector", "session", "customer"):
        mem.setdefault(k, True)

    s.setdefault("integrations", [])
    dep = s.setdefault("deployment", {})
    dep.setdefault("mode", "docker")
    dep.setdefault("channels", ["web"])

    if errors and not autofix:
        raise SpecValidationError("; ".join(errors))
    s["_validation"] = {"errors_fixed": errors} if errors else {"errors_fixed": []}
    return s


def _match_business_type(prompt: str) -> Optional[str]:
    p = (prompt or "").lower()
    best, best_hits = None, 0
    for btype, words in _BUSINESS_KEYWORDS.items():
        hits = sum(1 for w in words if w in p)
        if hits > best_hits:
            best, best_hits = btype, hits
    return best


def _extract_name(prompt: str) -> Optional[str]:
    m = re.search(r"(?:called|named)\s+['\"]?([A-Z][\w'&\- ]{2,40})['\"]?", prompt or "")
    return m.group(1).strip() if m else None


def _customize_template(template: dict, prompt: str, business_type: str) -> dict:
    spec = copy.deepcopy(template)
    name = _extract_name(prompt)
    if name:
        old = spec.get("name", "")
        spec["name"] = f"{name} Assistant"
        for a in spec.get("agents", []):
            a["system_prompt"] = a.get("system_prompt", "").replace(old.replace(" Assistant", ""), name)
    if prompt:
        spec["description"] = (spec.get("description", "") +
                               f" Customized from requirement: {prompt[:300]}")
    return validate_spec(spec)


_GEN_PROMPT = """You design AI agent teams. Produce ONLY a JSON AgentSpec with keys:
version, name, business_type, description, model_policy, agents (2-4 agents, each
with id, role, system_prompt of 100+ words, tools from [faq_rag, booking,
google_calendar, gmail, twilio_sms, whatsapp, slack, stripe, shopify, hubspot,
salesforce, zapier, n8n_webhook, custom_api, webhook, database_query, google_maps],
memory, model:"auto"), supervisor {{enabled, routing_prompt}}, workflow {{nodes with
id/type/ref/position{{x,y}}, edges}}, tools, rag, memory, integrations, deployment.
Requirement: {prompt}
Business type: {business_type}
Return only JSON, no markdown fences."""


async def generate_agent_spec(prompt: str, business_type: str | None = None) -> dict:
    """Generate a complete, valid AgentSpec from a natural-language requirement."""
    from ..templates import get_template, list_templates

    known = {t["business_type"] for t in list_templates()}

    # 1. Explicit business type that matches a template.
    if business_type and business_type in known:
        return _customize_template(get_template(business_type), prompt, business_type)

    # 2. LLM generation via the router.
    choice = select_model("agent spec generation", {"priority": "accuracy",
                                                    "require_available": True})
    llm = get_chat_model(choice["provider"], choice["model"], temperature=0.2)
    if llm is not None:
        try:
            msg = await llm.ainvoke(_GEN_PROMPT.format(prompt=prompt,
                                                       business_type=business_type or "infer"))
            raw = getattr(msg, "content", "")
            raw = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.M).strip()
            spec = json.loads(raw)
            spec.setdefault("business_type", business_type or _match_business_type(prompt) or "generic")
            return validate_spec(spec)
        except Exception:
            pass  # fall through to heuristics

    # 3. Heuristic: keyword-match the prompt against templates.
    matched = _match_business_type(prompt) or (business_type if business_type in known else None)
    if matched and matched in known:
        return _customize_template(get_template(matched), prompt, matched)

    # 4. Generic multi-agent spec from role presets.
    name = _extract_name(prompt) or "Business Assistant"
    btype = business_type or "generic"
    agents = [
        build_role("receptionist", name, btype),
        build_role("booking", name, btype),
        build_role("support", name, btype),
    ]
    spec = {
        "version": 1,
        "name": f"{name} Agent Team",
        "business_type": btype,
        "description": f"Auto-generated (heuristic, stub=true) from: {prompt[:300]}",
        "model_policy": {"preferred": "auto",
                         "constraints": {"max_cost_per_1k_tokens": 0.01,
                                         "min_context": 32000, "priority": "balanced"}},
        "agents": agents,
        "supervisor": {"enabled": True, "routing_prompt": ""},
        "workflow": _default_workflow(agents),
        "tools": [],
        "rag": {"enabled": True, "vector_store": "pgvector",
                "embedding_model": "text-embedding-3-small",
                "sources": [{"type": "faq", "description": "Business FAQ"}]},
        "memory": {"short_term": True, "long_term": True, "vector": True,
                   "session": True, "customer": True},
        "integrations": ["whatsapp", "gmail"],
        "deployment": {"mode": "docker", "channels": ["web"]},
        "stub": True,
    }
    return validate_spec(spec)


__all__ = ["generate_agent_spec", "validate_spec", "SpecValidationError"]
