"""Integrations CRUD router (credentials never returned in reads)."""
from app.api.v1.crud_factory import build_crud_router
from app.models import Integration
from app.schemas.content import IntegrationCreate, IntegrationRead, IntegrationUpdate

router, service = build_crud_router(
    prefix="/integrations",
    tag="integrations",
    resource="integration",
    model=Integration,
    read_schema=IntegrationRead,
    create_schema=IntegrationCreate,
    update_schema=IntegrationUpdate,
    search_fields=("provider", "name"),
    write_role="admin",
    delete_role="admin",
)
