from fastapi import APIRouter

from .endpoints import router as endpoints_router

router = APIRouter(prefix="/auth")

router.include_router(endpoints_router)