from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # App Configuration
    APP_NAME: str = "FIDEAS - Enterprise Management System"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database Configuration
    DATABASE_URL: str = "postgresql://postgres:admin@localhost:5432/fideas_enterprise_1"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    
    # Security Configuration
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    
    # Server Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()