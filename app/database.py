from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Создаем engine для подключения к базе данных
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # Показывать SQL запросы в консоли при DEBUG=True
    pool_pre_ping=True,   # Проверять соединение перед использованием
    pool_recycle=300      # Пересоздавать соединения каждые 5 минут
)

# Создаем фабрику сессий
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Создаем базовый класс для моделей
Base = declarative_base()

# Функция для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Функция для создания всех таблиц
def create_tables():
    Base.metadata.create_all(bind=engine)