"""
API клиент для Wildberries маркетплейса
"""
import logging
from typing import List, Optional, Dict, Any
from urllib.parse import quote

from .base_api import BaseMarketplaceAPI, ProductInfo, ProductNotFoundError

logger = logging.getLogger(__name__)


class WildberriesAPI(BaseMarketplaceAPI):
    """API клиент для Wildberries"""
    
    BASE_URL_SEARCH = "https://search.wb.ru/exactmatch/ru/common/v5/search"
    BASE_URL_PRODUCT = "https://card.wb.ru/cards/v2/detail"
    BASE_URL_IMAGES = "https://basket-{basket:02d}.wbbasket.ru/vol{vol}/part{part}/{nm}/images/c516x688/{index}.jpg"
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        self._last_search_results = []
    
    @property
    def marketplace_name(self) -> str:
        return "wildberries"
    
    async def search_products(self, query: str, limit: int = 10) -> List[ProductInfo]:
        try:
            logger.info(f"Wildberries search: '{query}'")
            
            params = {
                'query': query,
                'resultset': 'catalog',
                'limit': min(limit, 300),
                'sort': 'popular',
                'page': 1,
                'TestGroup': 'no_test',
                'TestID': 'no_test',
                'locale': 'ru'
            }
            
            data = await self._make_request('GET', self.BASE_URL_SEARCH, params=params)
            
            products = []
            items = data.get('data', {}).get('products', [])
            
            self._last_search_results = items
            
            for item in items[:limit]:
                try:
                    product = await self._parse_product_item(item)
                    if product:
                        products.append(product)
                except Exception as e:
                    logger.warning(f"Error parsing product: {e}")
                    continue
            
            return products
            
        except Exception as e:
            logger.error(f"Wildberries search error: {e}")
            return []
    
    async def get_product_by_id(self, product_id: str) -> Optional[ProductInfo]:
        try:
            if hasattr(self, '_last_search_results'):
                for item in self._last_search_results:
                    if str(item.get('id', '')) == str(product_id):
                        return await self._parse_product_item(item)
            
            logger.info(f"Wildberries get product by ID: {product_id}")
            
            params = {
                'nm': product_id,
                'curr': 'rub',
                'dest': -1257786
            }
            
            data = await self._make_request('GET', self.BASE_URL_PRODUCT, params=params)
            
            products_data = data.get('data', {}).get('products', [])
            if not products_data:
                return None
            
            for product_data in products_data:
                if str(product_data.get('id', '')) == str(product_id):
                    return await self._parse_product_item(product_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting Wildberries product {product_id}: {e}")
            return None
    
    async def _parse_product_item(self, item: Dict[str, Any]) -> Optional[ProductInfo]:
        try:
            product_id = str(item.get('id', ''))
            if not product_id:
                return None
            
            name = item.get('name', '') or item.get('title', '')
            if not name:
                return None
            
            sizes = item.get('sizes', [])
            if not sizes or not sizes[0].get('price', {}).get('product'):
                return None
            
            price_kopecks = sizes[0]['price']['product']
            price = price_kopecks / 100.0
            
            available = item.get('totalQuantity', 0) > 0
            
            product_url = f"https://www.wildberries.ru/catalog/{product_id}/detail.aspx"
            
            nm = item.get('id')
            basket = (nm // 100000) % 100 if nm else 1
            vol = nm // 100000 if nm else 1
            part = nm // 1000 if nm else 1
            image_url = self.BASE_URL_IMAGES.format(
                basket=basket,
                vol=vol,
                part=part,
                nm=nm,
                index=1
            ) if nm else None
            
            return ProductInfo(
                marketplace="wildberries",
                product_id=product_id,
                name=name,
                price=price,
                currency="RUB",
                url=product_url,
                image_url=image_url,
                rating=item.get('rating', 0.0),
                reviews_count=item.get('feedbacks', 0),
                availability=available,
                brand=item.get('brand', ''),
                seller=item.get('supplier', '')
            )
            
        except Exception as e:
            logger.error(f"Error parsing Wildberries product: {e}")
            return None


def create_wildberries_client(api_key: Optional[str] = None) -> WildberriesAPI:
    return WildberriesAPI(api_key) 