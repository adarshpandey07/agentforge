"""Auth service: tenant+owner registration, login, token issuance."""
import re
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import create_access_token, hash_password, verify_password
from app.models import Tenant, User
from app.schemas.auth import LoginRequest, RegisterRequest


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "tenant"
    return f"{slug}-{uuid.uuid4().hex[:6]}"


async def register_tenant(db: AsyncSession, payload: RegisterRequest) -> tuple[User, str]:
    """Create a new tenant with its owner user. Returns (user, access_token)."""
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalars().first() is not None:
        raise ConflictError("A user with this email already exists")

    tenant = Tenant(name=payload.tenant_name, slug=_slugify(payload.tenant_name))
    db.add(tenant)
    await db.flush()

    user = User(
        tenant_id=tenant.id,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role="owner",
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(subject=user.id, tenant_id=user.tenant_id, role=user.role)
    return user, token


async def authenticate(db: AsyncSession, payload: LoginRequest) -> tuple[User, str]:
    """Verify credentials and issue a JWT. Raises UnauthorizedError on failure."""
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalars().first()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise UnauthorizedError("Invalid email or password")
    if not user.is_active:
        raise UnauthorizedError("User is deactivated")
    token = create_access_token(subject=user.id, tenant_id=user.tenant_id, role=user.role)
    return user, token
