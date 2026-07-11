from fastapi import APIRouter

from .login import router as login_router

router = APIRouter(prefix="/auth")

router.include_router(login_router)