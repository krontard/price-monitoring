"""
Основное приложение FastAPI
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db, close_db
from .api.v1.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title="Arbitration API",
    description="API для арбитража товаров между маркетплейсами",
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

try:
    app.include_router(api_router, prefix="/api/v1")
except Exception as e:
    logging.error(f"Failed to include API router: {e}")


@app.get("/")
async def root():
    return {"message": "Arbitration API is running!"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "API is working correctly"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )