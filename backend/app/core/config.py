from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from pydantic import model_validator
from urllib.parse import quote_plus

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Timetable Generator"
    PROJECT_VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    ENV: str = "dev"
    
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "timetable_db"
    SQLALCHEMY_DATABASE_URI: Optional[str] = None
    DATABASE_URL: Optional[str] = None # Added to prevent extra field error
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "development_secret_key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440 # 24 hours
    
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "http://localhost:8000"]

    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    OLLAMA_MODEL: str = "llama3.1"

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="ignore"
    )

    @model_validator(mode='after')
    def assemble_db_connection(self):
        if not self.SQLALCHEMY_DATABASE_URI:
            # Prefer DATABASE_URL if provided, else assemble from POSTGRES_*
            if self.DATABASE_URL:
                self.SQLALCHEMY_DATABASE_URI = self.DATABASE_URL
            else:
                password = quote_plus(self.POSTGRES_PASSWORD)
                self.SQLALCHEMY_DATABASE_URI = f"postgresql://{self.POSTGRES_USER}:{password}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"
        
        return self

settings = Settings()
