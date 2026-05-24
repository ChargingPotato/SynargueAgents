from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"extra": "allow", "env_file": ".env", "env_prefix": "DP_"}

    app_title: str = "Synargue API"
    app_version: str = "2.0.0"
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    debug: bool = True
    redis_url: str = "redis://localhost:6379/0"


settings = Settings()
