from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # База данных PostgreSQL
    DATABASE_URL: str = "postgresql://postgres:1314@localhost:5432/arbitration_db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # RabbitMQ
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"
    
    # Внешние API ключи
    AMAZON_API_KEY: Optional[str] = None
    WILDBERRIES_API_KEY: Optional[str] = None
    OZON_API_KEY: Optional[str] = None
    
    # Настройки приложения
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    
    # Настройки сервера
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Настройки уведомлений
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Добавьте эту строку

settings = Settings()