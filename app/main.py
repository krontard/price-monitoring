from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.database import create_tables
from app.api.v1.api import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Запуск приложения...")
    try:
        create_tables()
        print("✅ Таблицы базы данных созданы!")
    except Exception as e:
        print(f"❌ Ошибка создания таблиц: {e}")
    yield
    print("🛑 Остановка приложения...")

app = FastAPI(
    title="Arbitration Price Monitoring",
    description="Система мониторинга цен на товары",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Попробуем подключить роутеры с обработкой ошибок
try:
    from app.api.v1.api import api_router
    app.include_router(api_router, prefix="/api/v1")
    print("✅ API роутеры подключены успешно!")
except Exception as e:
    print(f"❌ Ошибка подключения API роутеров: {e}")

@app.get("/")
async def root():
    return {
        "message": "Arbitration Price Monitoring API",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/info")
async def get_info():
    return {
        "name": "Arbitration Price Monitoring",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
    }