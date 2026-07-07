"""JWT creation/verification and password / API-key hashing."""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings
from app.core.exceptions import UnauthorizedError


def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt (input pre-hashed so length is unbounded)."""
    digest = hashlib.sha256(password.encode()).hexdigest().encode()
    return bcrypt.hashpw(digest, bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against its bcrypt hash."""
    digest = hashlib.sha256(plain.encode()).hexdigest().encode()
    try:
        return bcrypt.checkpw(digest, hashed.encode())
    except ValueError:
        return False


def create_access_token(
    *, subject: str, tenant_id: str, role: str, expires_minutes: int | None = None
) -> str:
    """Create a signed JWT with `sub`, `tenant_id` and `role` claims."""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload: dict[str, Any] = {
        "sub": subject,
        "tenant_id": tenant_id,
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT. Raises UnauthorizedError on any failure."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError as exc:
        raise UnauthorizedError("Invalid or expired token") from exc
    if not payload.get("sub"):
        raise UnauthorizedError("Token missing subject claim")
    return payload


def hash_api_key(key: str) -> str:
    """Deterministic sha256 hash used to store/verify API keys."""
    return hashlib.sha256(key.encode()).hexdigest()


def generate_api_key() -> tuple[str, str, str]:
    """Generate a new API key. Returns (plaintext, prefix, hashed)."""
    plaintext = f"af_{secrets.token_urlsafe(32)}"
    return plaintext, plaintext[:11], hash_api_key(plaintext)
