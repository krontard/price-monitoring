from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List, Optional
from datetime import datetime, timedelta
from app.database import get_async_db
from app.models.price_history import PriceHistory
from app.models.product import Product
from app.schemas.price_history import (
    PriceHistory as PriceHistorySchema,
    PriceHistoryCreate,
    PriceHistoryList,
    PriceComparison
)

router = APIRouter()

@router.get("/{product_id}/history", response_model=PriceHistoryList)
async def get_price_history(
    product_id: int,
    marketplace: Optional[str] = Query(None, description="Фильтр по маркетплейсу"),
    days: int = Query(30, description="Количество дней для получения истории"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Получить историю цен для продукта
    """
    # Проверяем существование продукта
    result = await db.execute(
        select(Product).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Продукт не найден")
    
    # Строим запрос для истории цен
    query = select(PriceHistory).where(
        PriceHistory.product_id == product_id,
        PriceHistory.created_at >= datetime.utcnow() - timedelta(days=days)
    )
    
    if marketplace:
        query = query.where(PriceHistory.marketplace == marketplace)
    
    query = query.order_by(desc(PriceHistory.created_at))
    
    result = await db.execute(query)
    price_history = result.scalars().all()
    
    return PriceHistoryList(
        product_id=product_id,
        product_name=product.name,
        total_records=len(price_history),
        history=price_history
    )

@router.post("/{product_id}/history", response_model=PriceHistorySchema)
async def create_price_history(
    product_id: int,
    price_data: PriceHistoryCreate,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Добавить запись о цене продукта
    """
    # Проверяем существование продукта
    result = await db.execute(
        select(Product).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Продукт не найден")
    
    # Создаем запись истории цен
    db_price_history = PriceHistory(
        product_id=product_id,
        **price_data.model_dump()
    )
    
    db.add(db_price_history)
    await db.commit()
    await db.refresh(db_price_history)
    
    return db_price_history

@router.get("/{product_id}/comparison", response_model=PriceComparison)
async def get_price_comparison(
    product_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Сравнить последние цены по всем маркетплейсам
    """
    # Проверяем существование продукта
    result = await db.execute(
        select(Product).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Продукт не найден")
    
    # Получаем последние цены по каждому маркетплейсу
    marketplaces = ['amazon', 'wildberries', 'ozon']
    prices = []
    
    for marketplace in marketplaces:
        # Получаем последнюю цену для каждого маркетплейса
        result = await db.execute(
            select(PriceHistory)
            .where(
                PriceHistory.product_id == product_id,
                PriceHistory.marketplace == marketplace
            )
            .order_by(desc(PriceHistory.created_at))
            .limit(1)
        )
        latest_price = result.scalar_one_or_none()
        
        if latest_price:
            prices.append({
                "marketplace": marketplace,
                "price": latest_price.price,
                "currency": latest_price.currency,
                "last_updated": latest_price.created_at
            })
    
    if not prices:
        raise HTTPException(
            status_code=404, 
            detail="История цен для данного продукта не найдена"
        )
    
    # Находим минимальную и максимальную цены
    min_price = min(prices, key=lambda x: x["price"])
    max_price = max(prices, key=lambda x: x["price"])
    
    # Вычисляем потенциальную прибыль
    arbitrage_opportunity = max_price["price"] - min_price["price"]
    
    return PriceComparison(
        product_id=product_id,
        product_name=product.name,
        prices=prices,
        min_price=min_price,
        max_price=max_price,
        arbitrage_opportunity=arbitrage_opportunity,
        comparison_date=datetime.utcnow()
    )

@router.get("/latest", response_model=List[PriceHistorySchema])
async def get_latest_prices(
    limit: int = Query(50, description="Количество последних записей"),
    marketplace: Optional[str] = Query(None, description="Фильтр по маркетплейсу"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Получить последние обновления цен
    """
    query = select(PriceHistory).order_by(desc(PriceHistory.created_at))
    
    if marketplace:
        query = query.where(PriceHistory.marketplace == marketplace)
    
    query = query.limit(limit)
    
    result = await db.execute(query)
    price_history = result.scalars().all()
    
    return price_history 