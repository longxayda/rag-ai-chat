from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "RAG server"
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_port: int
    
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')


# Using lru_cache ensures we only load the .env file once, not on every request
@lru_cache
def get_settings():
    return Settings()

settings = get_settings()