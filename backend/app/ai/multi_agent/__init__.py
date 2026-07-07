"""Multi-agent package: supervisor routing + team role presets."""
from .supervisor import build_routing_prompt, route, route_deterministic  # noqa: F401
from .teams import ROLE_PRESETS, build_role  # noqa: F401

__all__ = ["build_routing_prompt", "route", "route_deterministic",
           "ROLE_PRESETS", "build_role"]
