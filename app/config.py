from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@db:5432/analytics"
    sync_database_url: str = "postgresql+psycopg2://postgres:postgres@db:5432/analytics"
    redis_url: str = "redis://redis:6379/0"
    groq_api_key: str = ""

    model_config = {"env_file": ".env"}


settings = Settings()
