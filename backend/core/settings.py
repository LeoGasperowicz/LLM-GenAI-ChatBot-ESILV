from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "ESILV Smart Assistant API"
    API_V1_PREFIX: str = "/api"

    LLM_PROVIDER: str = "ollama"
    LLM_MODEL: str = "mistral"
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    FRONTEND_ORIGIN: str = "http://localhost:8501"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
