"""Auth endpoints: register, login, me."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserRead
from app.services.auth import authenticate, register_tenant

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    """Create a new tenant plus its owner user and return an access token."""
    user, token = await register_tenant(db, payload)
    return TokenResponse(access_token=token, user=UserRead.model_validate(user))


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    """Exchange email/password for a JWT access token."""
    user, token = await authenticate(db, payload)
    return TokenResponse(access_token=token, user=UserRead.model_validate(user))


@router.get("/me", response_model=UserRead)
async def me(user: User = Depends(get_current_user)) -> User:
    """Return the authenticated user."""
    return user
