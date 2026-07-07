"""FastAPI dependencies: DB session, current user, RBAC."""
from collections.abc import Callable, Coroutine
from typing import Any

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import User

__all__ = ["get_db", "get_current_user", "require_role"]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

ROLE_RANK: dict[str, int] = {"viewer": 0, "member": 1, "admin": 2, "owner": 3}


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Resolve the authenticated user from a Bearer JWT."""
    if not token:
        raise UnauthorizedError("Missing bearer token")
    payload = decode_access_token(token)
    user = await db.get(User, payload["sub"])
    if user is None or not user.is_active:
        raise UnauthorizedError("User not found or inactive")
    return user


def require_role(*roles: str) -> Callable[..., Coroutine[Any, Any, User]]:
    """RBAC dependency. Grants access when the user's role rank is >= the
    minimum rank among the given roles (owner > admin > member > viewer)."""
    minimum = min((ROLE_RANK.get(r, 0) for r in roles), default=ROLE_RANK["member"])

    async def checker(user: User = Depends(get_current_user)) -> User:
        if ROLE_RANK.get(user.role, -1) < minimum:
            raise ForbiddenError(f"Requires one of roles: {', '.join(roles)}")
        return user

    return checker
