from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import db_provider
from src.domains.auth.models import User
from src.domains.auth.service import create_access_token, decode_token, needs_renewal

security_scheme = HTTPBearer()
optional_security_scheme = HTTPBearer(auto_error=False)


async def require_auth(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> dict:
    """
    Validate Bearer token and return payload dict.
    Does NOT query the database — only verifies JWT signature and expiry.

    Use this for endpoints that just need to know "is this user logged in?"
    """
    try:
        payload = decode_token(credentials.credentials)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Auto-renew: if token is nearing expiry, issue a new one via response header
    if needs_renewal(payload):
        new_token = create_access_token(
            user_id=payload["user_id"],
            username=payload["sub"],
            email=payload.get("email", ""),
        )
        request.state.new_access_token = new_token

    return payload


async def get_current_user(
    payload: dict = Depends(require_auth),
    db: AsyncSession = Depends(db_provider.get_db_session),
) -> User:
    """
    Validate token AND fetch the full User object from DB.

    Use this for endpoints that need user details (e.g. /api/auth/me).
    """
    user = await db.get(User, payload["user_id"])
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security_scheme),
    db: AsyncSession = Depends(db_provider.get_db_session),
) -> User | None:
    """
    If a valid Bearer token is present, return the User. Otherwise return None.

    Use this for endpoints that support both anonymous and authenticated access.
    """
    if credentials is None:
        return None
    try:
        payload = decode_token(credentials.credentials)
        return await db.get(User, payload["user_id"])
    except Exception:
        return None
