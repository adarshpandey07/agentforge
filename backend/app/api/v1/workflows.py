"""Workflows CRUD router."""
from app.api.v1.crud_factory import build_crud_router
from app.models import Workflow
from app.schemas.business import WorkflowCreate, WorkflowRead, WorkflowUpdate

router, service = build_crud_router(
    prefix="/workflows",
    tag="workflows",
    resource="workflow",
    model=Workflow,
    read_schema=WorkflowRead,
    create_schema=WorkflowCreate,
    update_schema=WorkflowUpdate,
)
