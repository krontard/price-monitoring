"""
Конфигурация приложения
"""
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/arbitration"
    
    REDIS_URL: str = "redis://localhost:6379/0"
    
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"
    
    WILDBERRIES_API_KEY: str = ""
    OZON_CLIENT_ID: str = ""
    OZON_API_KEY: str = ""
    
    APP_NAME: str = "Arbitration API"
    DEBUG: bool = True
    SECRET_KEY: str = "your-secret-key-here"
    
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    EMAIL_USERNAME: str = ""
    EMAIL_PASSWORD: str = ""
    
    class Config:
        env_file = ".env"

settings = Settings()