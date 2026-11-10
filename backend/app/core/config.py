from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application runtime configuration with environment variable support."""

    PROJECT_NAME: str = "JobShield AI"
    VERSION: str = "0.2.0"
    API_V1_PREFIX: str = "/api"
    ENVIRONMENT: str = "development"

    # Restrict CORS to local frontend development hosts
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # Model status tracking (honest lifecycle reporting)
    MODEL_STATUS: str = "trained"
    ACTIVE_MODEL_NAME: str = "Linear Support Vector Machine"

    # LLM & Explanation Configuration
    # Set LLM_PROVIDER=none (default) to run entirely offline with local deterministic engine.
    # Set LLM_PROVIDER=groq and provide LLM_API_KEY to enable optional AI-enhanced explanations.
    LLM_PROVIDER: str = "none"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "llama-3.3-70b-versatile"
    LLM_TEMPERATURE: float = 0.1
    LLM_TIMEOUT: int = 30

    # URL Extraction & Security
    URL_FETCH_TIMEOUT: int = 10
    MAX_URL_CONTENT_BYTES: int = 2 * 1024 * 1024  # 2 MB limit

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
        protected_namespaces=(),
    )


settings = Settings()
