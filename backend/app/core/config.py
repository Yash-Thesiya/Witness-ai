from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    #Database
    DATABASE_URL: str = "postgresql://witness:witness@db:5432/witness_db"

    #JWT
    SECRET_KEY: str = "your-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    #App
    APP_NAME: str = "Witness"
    ENVIRONMENT: str = "development"

    # Redis + Celery
    REDIS_URL: str = "redis://redis:6379/0"

    # Openrouter AI
    OPENROUTER_API_KEY: str = "your-openrouter-key"
    OPENROUTER_MODEL: str = "meta-llama/llama-3.1-8b-instruct:free"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    class Config:
        env_file = ".env"


settings = Settings()
