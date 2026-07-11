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
    ALLOW_ORIGINS: list[str] = []

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def is_production(self) -> bool:
        return self.ENV == Environment.PRODUCTION
    

settings = Settings()