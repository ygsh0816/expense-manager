from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    # Django settings
    SECRET_KEY: str
    DEBUG: bool = False

    # Database
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int = 5432

    # Stream consumer
    CASHCOG_STREAM_URL: str = ""
    CASHCOG_SINGLE_EXPENSE_URL: str = ""
    STREAM_PROCESSING_MAX_RETRIES: int = 3
    DEFAULT_STREAM_TYPE: Literal["expense", "invoice"] = "expense"

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"


settings = Settings()
