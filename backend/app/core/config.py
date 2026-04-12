from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    app_name: str = "DataWhisperer"
    debug: bool = True

    model_config = ConfigDict(
        env_file=".env",
        extra="ignore"
    )

settings = Settings()