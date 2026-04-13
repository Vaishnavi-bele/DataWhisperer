from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "DataWhisperer"
    debug: bool = True

    # LLM
    llm_model: str = "google/flan-t5-base"
    llm_max_tokens: int = 200
    openai_api_key: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()