"""Projects CRUD router."""
from app.api.v1.crud_factory import build_crud_router
from app.models import Project
from app.schemas.business import ProjectCreate, ProjectRead, ProjectUpdate

router, service = build_crud_router(
    prefix="/projects",
    tag="projects",
    resource="project",
    model=Project,
    read_schema=ProjectRead,
    create_schema=ProjectCreate,
    update_schema=ProjectUpdate,
    search_fields=("name", "description"),
)
