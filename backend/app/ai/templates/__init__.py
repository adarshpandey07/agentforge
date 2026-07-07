"""Business template marketplace: AgentSpec JSONs shipped with the platform."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

_TEMPLATE_DIR = Path(__file__).parent


@lru_cache(maxsize=1)
def _load_all() -> dict[str, dict]:
    specs: dict[str, dict] = {}
    for path in sorted(_TEMPLATE_DIR.glob("*.json")):
        try:
            spec = json.loads(path.read_text(encoding="utf-8"))
            specs[spec.get("business_type", path.stem)] = spec
        except Exception:
            continue
    return specs


def list_templates() -> list[dict]:
    """Summaries of every shipped template (marketplace listing)."""
    out = []
    for btype, spec in _load_all().items():
        out.append({
            "business_type": btype,
            "name": spec.get("name", btype.title()),
            "description": spec.get("description", ""),
            "agents": [a.get("role", a.get("id")) for a in spec.get("agents", [])],
            "tools": sorted({t for a in spec.get("agents", []) for t in a.get("tools", [])}),
            "integrations": spec.get("integrations", []),
            "supervisor": bool((spec.get("supervisor") or {}).get("enabled")),
        })
    return out


def get_template(business_type: str) -> dict:
    """Full AgentSpec for a business type. Raises KeyError when unknown."""
    specs = _load_all()
    key = (business_type or "").strip().lower().replace("-", "_").replace(" ", "_")
    if key not in specs:
        raise KeyError(
            f"No template for business_type '{business_type}'. "
            f"Available: {sorted(specs)}"
        )
    return json.loads(json.dumps(specs[key]))  # deep copy


__all__ = ["list_templates", "get_template"]
