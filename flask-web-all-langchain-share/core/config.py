from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str | None = None
    debug: bool = False
    
    ai_provider: str | None = None

    gemini_api_key: str | None = None
    gemini_model_name: str | None = None

    azure_openai_endpoint: str | None = None
    azure_openai_api_key: str | None = None
    azure_openai_deployment_name: str | None = None

    lmstudio_base_url: str | None = None
    lmstudio_model_name: str | None = None
    lmstudio_api_key: str | None = None

    ollama_model_name: str | None = None

    class Config:
        env_file = ".env"


@lru_cache
def get_settings():
    return Settings()