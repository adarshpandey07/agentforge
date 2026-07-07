"""Clients CRUD router."""
from app.api.v1.crud_factory import build_crud_router
from app.models import Client
from app.schemas.business import ClientCreate, ClientRead, ClientUpdate

router, service = build_crud_router(
    prefix="/clients",
    tag="clients",
    resource="client",
    model=Client,
    read_schema=ClientRead,
    create_schema=ClientCreate,
    update_schema=ClientUpdate,
    search_fields=("name", "business_type", "contact_email"),
)
