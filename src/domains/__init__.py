from fastapi import APIRouter

from .auth import router as auth_router
from .agent.router import router as agent_router

router = APIRouter(prefix="/api")

router.include_router(auth_router)
router.include_router(agent_router)
