from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.database import get_async_db
from app.models.product import Product
from app.schemas.product import Product as ProductSchema, ProductCreate, ProductUpdate

router = APIRouter()

@router.post("/", response_model=ProductSchema, status_code=status.HTTP_201_CREATED)
async def create_product(
    product: ProductCreate, 
    db: AsyncSession = Depends(get_async_db)
):
    """
    Создать новый продукт для мониторинга
    """
    # Преобразуем HttpUrl в строки для сохранения в БД
    product_data = product.model_dump()
    if product_data.get('amazon_url'):
        product_data['amazon_url'] = str(product_data['amazon_url'])
    if product_data.get('wildberries_url'):
        product_data['wildberries_url'] = str(product_data['wildberries_url'])
    if product_data.get('ozon_url'):
        product_data['ozon_url'] = str(product_data['ozon_url'])
    
    db_product = Product(**product_data)
    
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)
    
    return db_product

@router.get("/", response_model=List[ProductSchema])
async def read_products(
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_async_db)
):
    """
    Получить список продуктов
    """
    result = await db.execute(
        select(Product).offset(skip).limit(limit)
    )
    products = result.scalars().all()
    return products

@router.get("/{product_id}", response_model=ProductSchema)
async def read_product(
    product_id: int, 
    db: AsyncSession = Depends(get_async_db)
):
    """
    Получить продукт по ID
    """
    result = await db.execute(
        select(Product).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    
    if product is None:
        raise HTTPException(status_code=404, detail="Продукт не найден")
    
    return product

@router.put("/{product_id}", response_model=ProductSchema)
async def update_product(
    product_id: int, 
    product_update: ProductUpdate, 
    db: AsyncSession = Depends(get_async_db)
):
    """
    Обновить данные продукта
    """
    result = await db.execute(
        select(Product).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    
    if product is None:
        raise HTTPException(status_code=404, detail="Продукт не найден")
    
    # Получаем данные для обновления
    update_data = product_update.model_dump(exclude_unset=True)
    
    # Преобразуем HttpUrl в строки
    if 'amazon_url' in update_data and update_data['amazon_url']:
        update_data['amazon_url'] = str(update_data['amazon_url'])
    if 'wildberries_url' in update_data and update_data['wildberries_url']:
        update_data['wildberries_url'] = str(update_data['wildberries_url'])
    if 'ozon_url' in update_data and update_data['ozon_url']:
        update_data['ozon_url'] = str(update_data['ozon_url'])
    
    # Обновляем поля
    for field, value in update_data.items():
        setattr(product, field, value)
    
    await db.commit()
    await db.refresh(product)
    
    return product

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int, 
    db: AsyncSession = Depends(get_async_db)
):
    """
    Удалить продукт
    """
    result = await db.execute(
        select(Product).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    
    if product is None:
        raise HTTPException(status_code=404, detail="Продукт не найден")
    
    await db.delete(product)
    await db.commit()
    
    return None