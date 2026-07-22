from fastapi import APIRouter, Depends
from redis.asyncio import Redis

from src.core.redis import redis_provider

router = APIRouter(prefix="/login")

@router.post("/web")
async def login_web():
    pass

@router.get("/test")
async def test(redis: Redis = Depends(redis_provider.get_redis_db0)):
    res = await redis.set("test", "hello, echo")
    return res