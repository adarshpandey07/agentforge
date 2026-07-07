"""Tools package: plugin registry + builtin integrations."""
from .registry import (  # noqa: F401
    TOOLS,
    ToolPlugin,
    get_tool,
    get_tools_for_spec,
    list_tools,
    register_tool,
)
from . import builtins  # noqa: F401  (registers the builtin catalog)

__all__ = ["TOOLS", "ToolPlugin", "get_tool", "get_tools_for_spec",
           "list_tools", "register_tool"]
