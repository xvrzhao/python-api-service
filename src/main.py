import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.logging import setup_logging
from src.core.config import settings
from src.core.middlewares.trace import TraceMiddleware
from src.domains import router

setup_logging()
logger = logging.getLogger(__name__)
logger.info("application environment variables: %s", settings.model_dump_json())

app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,     
    allow_origins=settings.ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TraceMiddleware)

app.include_router(router)