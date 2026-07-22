from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import db_provider
from src.domains.auth.dependencies import get_current_user
from src.domains.auth.models import User
from src.domains.auth.schemas import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from src.domains.auth.service import authenticate_user, create_access_token, create_user

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, db: AsyncSession = Depends(db_provider.get_db_session)):
    try:
        user = await create_user(db, req)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    access_token = create_access_token(
        user_id=user.id, username=user.username, email=user.email
    )
    return TokenResponse(access_token=access_token)


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(db_provider.get_db_session)):
    user = await authenticate_user(db, req.identifier, req.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    access_token = create_access_token(
        user_id=user.id, username=user.username, email=user.email
    )
    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return current_user
