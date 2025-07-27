"""
Celery задачи для мониторинга цен
"""
import asyncio
from datetime import datetime
from typing import Dict, List, Optional

from celery import current_app as celery_app
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.models.product import Product
from app.models.price_history import PriceHistory
from app.external.wildberries_api import WildberriesAPI
from app.external.ozon_api import OzonAPI
from app.external.yandex_market_api import YandexMarketAPI


@celery_app.task(bind=True)
def monitor_product_price(self, product_id: int, product_name: str):
    """Мониторинг цены конкретного товара"""
    return asyncio.run(_monitor_product_price_async(product_id, product_name))


async def _monitor_product_price_async(product_id: int, product_name: str) -> Dict:
    """Асинхронная функция мониторинга цены товара"""
    
    try:
        print(f"Парсим цену на Ozon для: {product_name}")
        
        print("Пока что заглушка")
        return {
            "status": "success",
            "product_id": product_id,
            "product_name": product_name,
            "prices": {
                "wildberries": None,
                "ozon": None,
                "yandex_market": None
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "product_id": product_id
        }


@celery_app.task
def monitor_product_prices(product_id: int):
    """Задача мониторинга цен товара на всех площадках"""
    return asyncio.run(_monitor_product_prices_async(product_id))


async def _monitor_product_prices_async(product_id: int) -> Dict:
    """Асинхронный мониторинг цен товара"""
    
    async with get_async_session() as session:
        try:
            product = await session.get(Product, product_id)
            if not product:
                return {"error": f"Product {product_id} not found"}
            
            print(f"Мониторинг цен для продукта: {product.name} (ID: {product_id})")
            
            prices = {}
            
            if product.wildberries_id:
                async with WildberriesAPI() as wb_api:
                    wb_price = await wb_api.get_product_price(product.wildberries_id)
                    prices['wildberries'] = wb_price
            
            if product.ozon_id:
                async with OzonAPI() as ozon_api:
                    ozon_price = await ozon_api.get_product_price(product.ozon_id)
                    prices['ozon'] = ozon_price
            
            if product.yandex_market_id:
                async with YandexMarketAPI() as ym_api:
                    ym_price = await ym_api.get_product_price(product.yandex_market_id)
                    prices['yandex_market'] = ym_price
            
            for marketplace, price in prices.items():
                if price and price > 0:
                    price_entry = PriceHistory(
                        product_id=product_id,
                        marketplace=marketplace,
                        price=price,
                        timestamp=datetime.utcnow()
                    )
                    session.add(price_entry)
            
            await session.commit()
            
            result = {
                "product_id": product_id,
                "product_name": product.name,
                "prices": prices,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            print(f"Результат мониторинга для {product.name}: {result}")
            
            return result
            
        except Exception as e:
            await session.rollback()
            return {"error": str(e), "product_id": product_id}


@celery_app.task
def monitor_all_products():
    """Задача мониторинга всех продуктов"""
    print("Запуск мониторинга всех продуктов")
    return asyncio.run(_monitor_all_products_async())


async def _monitor_all_products_async() -> List[Dict]:
    """Асинхронный мониторинг всех продуктов"""
    async with get_async_session() as session:
        try:
            result = await session.execute(
                "SELECT id, name FROM products WHERE is_active = TRUE"
            )
            products = result.fetchall()
            
            results = []
            for product_id, product_name in products:
                try:
                    result = await _monitor_product_prices_async(product_id)
                    results.append(result)
                except Exception as e:
                    results.append({
                        "error": str(e),
                        "product_id": product_id,
                        "product_name": product_name
                    })
            
            return results
            
        except Exception as e:
            return [{"error": str(e)}]