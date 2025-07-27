"""
API клиент для Яндекс.Маркет через публичный API
"""
import logging
import re
from typing import List, Optional, Dict, Any
from urllib.parse import quote, urlencode

from .base_api import BaseMarketplaceAPI, ProductInfo, ProductNotFoundError

logger = logging.getLogger(__name__)


class YandexMarketAPI(BaseMarketplaceAPI):
    """API клиент для Яндекс.Маркет через публичный API"""
    
    BASE_URL = "https://market.yandex.ru"
    SEARCH_URL = "https://market.yandex.ru/api/v2/catalog/search"
    PRODUCT_URL = "https://market.yandex.ru/api/v2/catalog/product"

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        self._last_search_results = []

    @property
    def marketplace_name(self) -> str:
        return "yandex_market"

    async def search_products(self, query: str, limit: int = 10) -> List[ProductInfo]:
        try:
            logger.info(f"Yandex.Market search: '{query}'")
            
            params = {
                'text': query,
                'numdoc': min(limit, 48),
                'lr': 213,
                'suggest': 1,
                'suggest_text': query
            }
            
            if not self.session:
                await self._init_session()
            
            self.session.headers.update({
                'Referer': 'https://market.yandex.ru/',
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json, text/javascript, */*; q=0.01',
            })
            
            data = await self._make_request('GET', self.SEARCH_URL, params=params)
            
            products = []
            if 'results' in data:
                items = data['results']
            elif 'entities' in data:
                items = data['entities'].get('product', {}).values()
            else:
                logger.warning("Unexpected API response format")
                return await self._search_fallback(query, limit)
            
            self._last_search_results = list(items)[:limit]
            
            for item in list(items)[:limit]:
                try:
                    product = await self._parse_product_item(item)
                    if product:
                        products.append(product)
                except Exception as e:
                    logger.warning(f"Error parsing product: {e}")
                    continue
            
            if not products:
                logger.warning("No products found, trying fallback")
                return await self._search_fallback(query, limit)
            
            return products
            
        except Exception as e:
            logger.error(f"Yandex.Market search error: {e}")
            return await self._search_fallback(query, limit)

    async def get_product_by_id(self, product_id: str) -> Optional[ProductInfo]:
        try:
            if hasattr(self, '_last_search_results'):
                for item in self._last_search_results:
                    if str(item.get('id', '')) == str(product_id):
                        return await self._parse_product_item(item)
            
            params = {
                'productId': product_id,
                'lr': 213
            }
            
            try:
                data = await self._make_request('GET', self.PRODUCT_URL, params=params)
                if 'product' in data:
                    return await self._parse_product_item(data['product'])
            except:
                pass
            
            search_results = await self.search_products(str(product_id), limit=10)
            for product in search_results:
                if product.product_id == str(product_id):
                    return product
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting Yandex.Market product {product_id}: {e}")
            return None

    async def _parse_product_item(self, item: Dict[str, Any]) -> Optional[ProductInfo]:
        try:
            product_id = str(item.get('id', ''))
            if not product_id:
                return None
            
            name = item.get('name', '') or item.get('title', '')
            if not name:
                return None
            
            price = 0.0
            if 'price' in item:
                if isinstance(item['price'], dict):
                    price = float(item['price'].get('value', 0))
                else:
                    price = float(item['price'])
            elif 'prices' in item and item['prices']:
                price = float(item['prices'][0].get('value', 0))
            elif 'defaultOffer' in item:
                offer_price = item['defaultOffer'].get('price', {})
                if isinstance(offer_price, dict):
                    price = float(offer_price.get('value', 0))
                else:
                    price = float(offer_price)
            
            product_url = f"https://market.yandex.ru/product/{product_id}"
            if 'slug' in item:
                product_url = f"https://market.yandex.ru/product/{item['slug']}/{product_id}"
            
            image_url = None
            if 'pictures' in item and item['pictures']:
                pic = item['pictures'][0]
                if isinstance(pic, dict):
                    image_url = pic.get('url', pic.get('original', ''))
                else:
                    image_url = str(pic)
            elif 'mainPhoto' in item:
                image_url = item['mainPhoto'].get('url', '')
            
            rating = item.get('rating', 0.0)
            reviews_count = item.get('opinions', 0) or item.get('reviewsCount', 0)
            
            if isinstance(rating, str):
                try:
                    rating = float(rating)
                except:
                    rating = 0.0
            
            brand = item.get('vendor', {}).get('name', '') if isinstance(item.get('vendor'), dict) else item.get('vendor', '')
            
            availability = item.get('isAvailable', True)
            
            return ProductInfo(
                marketplace="yandex_market",
                product_id=product_id,
                name=name,
                price=price,
                currency="RUB",
                url=product_url,
                image_url=image_url,
                rating=rating,
                reviews_count=reviews_count,
                availability=availability,
                brand=brand
            )
            
        except Exception as e:
            logger.error(f"Error parsing Yandex.Market product: {e}")
            return None

    async def _search_fallback(self, query: str, limit: int) -> List[ProductInfo]:
        try:
            fallback_url = f"https://market.yandex.ru/suggest-market"
            params = {
                'part': query,
                'lr': 213,
                'shopid': 0,
                'adult': 1
            }
            
            data = await self._make_request('GET', fallback_url, params=params)
            
            products = []
            items = data.get('items', [])
            
            for item in items[:limit]:
                if 'title' in item:
                    product_id = f"ym_{hash(item['title']) % 1000000}"
                    
                    price_match = re.search(r'(\d+)', item.get('description', ''))
                    price = float(price_match.group(1)) if price_match else 1000.0
                    
                    product = ProductInfo(
                        marketplace="yandex_market",
                        product_id=product_id,
                        name=item['title'],
                        price=price,
                        currency="RUB",
                        url=f"https://market.yandex.ru/search?text={quote(item['title'])}",
                        availability=True
                    )
                    products.append(product)
            
            return products
            
        except Exception as e:
            logger.error(f"Fallback search failed: {e}")
            return []


def create_yandex_market_client(api_key: Optional[str] = None) -> YandexMarketAPI:
    return YandexMarketAPI(api_key) 