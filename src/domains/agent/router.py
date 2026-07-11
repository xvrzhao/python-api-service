from fastapi import APIRouter

from .agent import router as agent_router

router = APIRouter(prefix="/agent")

router.include_router(agent_router)