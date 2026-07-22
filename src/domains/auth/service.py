from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.domains.auth.models import User
from src.domains.auth.schemas import RegisterRequest


# ---- Password hashing ----


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ---- JWT ----


def _create_token(data: dict, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_access_token(*, user_id: int, username: str, email: str) -> str:
    return _create_token(
        {"sub": username, "user_id": user_id, "email": email},
        timedelta(days=settings.JWT_EXPIRE_DAYS),
    )


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")


def needs_renewal(payload: dict) -> bool:
    """Check if token should be renewed (remaining lifetime < renew threshold)."""
    exp = payload.get("exp")
    if exp is None:
        return False
    expire_at = datetime.fromtimestamp(exp, tz=timezone.utc)
    remaining = expire_at - datetime.now(timezone.utc)
    return remaining < timedelta(days=settings.JWT_RENEW_DAYS)


# ---- User operations ----


async def create_user(db: AsyncSession, req: RegisterRequest) -> User:
    """Register a new user. Raises ValueError on duplicate username/email."""
    existing = await db.execute(
        select(User).where((User.username == req.username) | (User.email == req.email))
    )
    if existing.scalar_one_or_none():
        raise ValueError("Username or email already exists")

    user = User(
        username=req.username,
        email=req.email,
        hashed_password=hash_password(req.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, identifier: str, password: str) -> User | None:
    """Verify credentials. identifier can be username or email."""
    if "@" in identifier:
        stmt = select(User).where(User.email == identifier)
    else:
        stmt = select(User).where(User.username == identifier)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user
