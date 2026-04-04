from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # App
    app_name: str = "DataWhisperer"
    debug: bool = True

    # API
    api_prefix: str = "/api"

    # Database
    database_url: str = "sqlite:///./data.db"

    # LLM (future use)
    llm_model: str = "google/flan-t5-base"
    llm_max_tokens: int = 200

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

settings = Settings()