"""Tools CRUD router."""
from app.api.v1.crud_factory import build_crud_router
from app.models import Tool
from app.schemas.content import ToolCreate, ToolRead, ToolUpdate

router, service = build_crud_router(
    prefix="/tools",
    tag="tools",
    resource="tool",
    model=Tool,
    read_schema=ToolRead,
    create_schema=ToolCreate,
    update_schema=ToolUpdate,
    search_fields=("name", "type", "description"),
)
