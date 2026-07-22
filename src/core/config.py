from logging import getLogger
from enum import Enum

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = getLogger(__name__)

class Environment(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"


class Settings(BaseSettings):
    ENV: Environment
    APP_NAME: str = ""

    LLM_API_KEY: SecretStr
    LLM_MODEL: str
    LLM_CTX_WIN: int
    LLM_CTX_WIN_THRESHOLD: float
    LLM_CTX_WIN_SUM_KEEP: float

    ALLOW_ORIGINS: list[str] = []

    PG_HOST: str
    PG_PORT: int
    PG_DB: str
    PG_USER: str
    PG_PSW: SecretStr
    PG_CONN_MAX: int

    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_PSW: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def is_production(self) -> bool:
        return self.ENV == Environment.PRODUCTION
    
    @property
    def postgres_uri(self) -> str:
        return f"postgresql://{self.PG_USER}:{self.PG_PSW.get_secret_value()}@{self.PG_HOST}:{self.PG_PORT}/{self.PG_DB}?sslmode=disable"
    

settings = Settings()