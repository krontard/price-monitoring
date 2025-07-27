"""
Сервис для поиска и сопоставления товаров на разных маркетплейсах
"""
import logging
from typing import Optional
from dataclasses import dataclass

from app.external.wildberries_api import WildberriesAPI
from app.external.ozon_api import OzonAPI
from app.external.yandex_market_api import YandexMarketAPI
from app.external.base_api import ProductInfo, ProductMatcher

logger = logging.getLogger(__name__)


@dataclass
class ProductMatch:
    query: str
    wildberries: Optional[ProductInfo] = None
    ozon: Optional[ProductInfo] = None
    yandex_market: Optional[ProductInfo] = None
    
    @property
    def found_count(self) -> int:
        return sum([
            1 if self.wildberries else 0,
            1 if self.ozon else 0,
            1 if self.yandex_market else 0
        ])
    
    @property
    def min_price(self) -> float:
        prices = []
        if self.wildberries: prices.append(self.wildberries.price)
        if self.ozon: prices.append(self.ozon.price)
        if self.yandex_market: prices.append(self.yandex_market.price)
        return min(prices) if prices else 0.0
    
    @property
    def max_price(self) -> float:
        prices = []
        if self.wildberries: prices.append(self.wildberries.price)
        if self.ozon: prices.append(self.ozon.price)
        if self.yandex_market: prices.append(self.yandex_market.price)
        return max(prices) if prices else 0.0
    
    @property
    def arbitrage_opportunity(self) -> float:
        return self.max_price - self.min_price if self.found_count >= 2 else 0.0


class ProductMatchingService:
    def __init__(self):
        self.wildberries = WildberriesAPI()
        self.ozon = OzonAPI()
        self.yandex_market = YandexMarketAPI()
        
    async def __aenter__(self):
        await self.wildberries.__aenter__()
        await self.ozon.__aenter__()
        await self.yandex_market.__aenter__()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.wildberries.__aexit__(exc_type, exc_val, exc_tb)
        await self.ozon.__aexit__(exc_type, exc_val, exc_tb)
        await self.yandex_market.__aexit__(exc_type, exc_val, exc_tb)
        
    async def find_product_everywhere(self, query: str, limit: int = 20) -> ProductMatch:
        logger.info(f"Searching for '{query}' across all marketplaces")
        
        result = ProductMatch(query=query)
        
        try:
            wb_product = await self.wildberries.find_best_product(query, limit=limit)
            if wb_product:
                result.wildberries = wb_product
                logger.info(f"Wildberries: {wb_product.name} - {wb_product.price} ₽")
            else:
                logger.warning(f"Wildberries: товар не найден")
        except Exception as e:
            logger.error(f"Ошибка поиска на Wildberries: {e}")
        
        try:
            ozon_product = await self.ozon.find_best_product(query, limit=limit)
            if ozon_product:
                result.ozon = ozon_product
                logger.info(f"Ozon: {ozon_product.name} - {ozon_product.price} ₽")
            else:
                logger.warning(f"Ozon: товар не найден")
        except Exception as e:
            logger.error(f"Ошибка поиска на Ozon: {e}")
        
        try:
            yandex_product = await self.yandex_market.find_best_product(query, limit=20)
            if yandex_product:
                result.yandex_market = yandex_product
                logger.info(f"Яндекс.Маркет: {yandex_product.name} - {yandex_product.price} ₽")
            else:
                logger.warning(f"Яндекс.Маркет: товар не найден")
        except Exception as e:
            logger.error(f"Ошибка поиска на Яндекс.Маркет: {e}")
        
        logger.info(f"Search completed for '{query}': found {result.found_count} products")
        return result
    
    async def validate_product_match(self, match: ProductMatch) -> bool:
        if match.found_count < 2:
            return True
        
        products = []
        if match.wildberries:
            products.append(match.wildberries)
        if match.ozon:
            products.append(match.ozon)
        if match.yandex_market:
            products.append(match.yandex_market)
        
        for i in range(len(products)):
            for j in range(i + 1, len(products)):
                similarity = ProductMatcher.calculate_similarity(
                    products[i].name, 
                    products[j].name
                )
                if similarity < 0.3:
                    logger.warning(
                        f"Подозрительно разные товары:\n"
                        f"  {products[i].name}\n"  
                        f"  {products[j].name}\n"
                        f"  Схожесть: {similarity:.2f}"
                    )
                    return False
        
        return True
    
    def get_urls_for_database(self, match: ProductMatch) -> dict:
        return {
            'wildberries_url': match.wildberries.url if match.wildberries else None,
            'ozon_url': match.ozon.url if match.ozon else None,
            'yandex_market_url': match.yandex_market.url if match.yandex_market else None,
        }
    
    def get_ids_for_monitoring(self, match: ProductMatch) -> dict:
        return {
            'wildberries_id': match.wildberries.product_id if match.wildberries else None,
            'ozon_id': match.ozon.product_id if match.ozon else None,
            'yandex_market_id': match.yandex_market.product_id if match.yandex_market else None,
        } 