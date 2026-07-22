import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.logging import setup_logging
from src.core.config import settings
from src.core.middlewares.trace import TraceMiddleware
from src.core.middlewares.auth_renew import AuthRenewMiddleware
from src.core.agent import agent_provider
from src.core.redis import redis_provider
from src.core.db import db_provider
from src.domains import router

setup_logging()
logger = logging.getLogger(__name__)
logger.info("application environment variables: %s", settings.model_dump_json())

@asynccontextmanager
async def lifespan(app: FastAPI):
    db_provider.init(settings.postgres_async_uri)
    redis_provider.init()
    await agent_provider.init()
    yield
    await agent_provider.shutdown()
    await redis_provider.shutdown()
    await db_provider.shutdown()

app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(AuthRenewMiddleware)
app.add_middleware(TraceMiddleware)

app.include_router(router)