"""
API клиент для Ozon через HTML парсинг
"""
import logging
import re
from typing import List, Optional, Dict, Any
from urllib.parse import quote
import asyncio

from .base_api import BaseMarketplaceAPI, ProductInfo, ProductNotFoundError

logger = logging.getLogger(__name__)

try:
    from bs4 import BeautifulSoup
    BEAUTIFULSOUP_AVAILABLE = True
except ImportError:
    BEAUTIFULSOUP_AVAILABLE = False
    logger.warning("BeautifulSoup не установлен. HTML парсинг недоступен.")


class OzonAPI(BaseMarketplaceAPI):
    """API клиент для Ozon"""
    
    BASE_URL = "https://www.ozon.ru"

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        self._last_search_results = []

    @property
    def marketplace_name(self) -> str:
        return "ozon"

    async def search_products(self, query: str, limit: int = 10) -> List[ProductInfo]:
        if not BEAUTIFULSOUP_AVAILABLE:
            logger.error("BeautifulSoup не установлен. Установите: pip install beautifulsoup4")
            return []
        
        try:
            logger.info(f"Ozon HTML парсинг: поиск '{query}'")
            
            search_url = f"{self.BASE_URL}/search/"
            params = {
                'text': query,
                'from_global': 'true'
            }
            
            response = await self.session.get(search_url, params=params)
            
            if response.status_code == 403:
                return []
            
            response.raise_for_status()
        
            products = await self._parse_search_page(response.text, limit)
            
            self._last_search_results = [
                {'id': p.product_id, 'mock_data': False} for p in products
            ]
            
            await asyncio.sleep(1)
            
            return products
            
        except Exception as e:
            logger.error(f"Ozon search error: {e}")
            return []

    async def get_product_by_id(self, product_id: str) -> Optional[ProductInfo]:
        if not BEAUTIFULSOUP_AVAILABLE:
            logger.error("BeautifulSoup не установлен. Установите: pip install beautifulsoup4")
            return None
            
        try:
            if hasattr(self, '_last_search_results'):
                for product in self._last_search_results:
                    if str(product.get('id', '')) == str(product_id):
                        if not product.get('mock_data'):
                            return await self._get_product_from_cache(product_id)
            
            product_url = f"{self.BASE_URL}/product/{product_id}/"
            
            try:
                response = await self.session.get(product_url)
                if response.status_code == 403:
                    return None
                response.raise_for_status()
            except Exception:
                return None
            
            return await self._parse_product_page(response.text, product_id)
            
        except Exception as e:
            logger.error(f"Error getting Ozon product {product_id}: {e}")
            return None

    async def _parse_search_page(self, html: str, limit: int) -> List[ProductInfo]:
        try:
            soup = BeautifulSoup(html, 'html.parser')
            products = []
            
            selectors = [
                'div[data-widget="searchResultsV2"] article',
                '.tile-root',
                '[data-widget="searchResultsV2"] [data-widget="searchResultsItem"]'
            ]
            
            items = []
            for selector in selectors:
                items = soup.select(selector)
                if items:
                    break
            
            for item in items[:limit]:
                try:
                    product = await self._parse_search_item(item)
                    if product:
                        products.append(product)
                except Exception as e:
                    logger.warning(f"Error parsing search item: {e}")
                    continue
            
            return products
            
        except Exception as e:
            logger.error(f"Error parsing search page: {e}")
            return []

    async def _parse_search_item(self, item) -> Optional[ProductInfo]:
        try:
            name_selectors = [
                'a[data-widget="searchResultsItem"] span',
                '.tile-hover-target span',
                'h3 a span'
            ]
            
            name = ""
            for selector in name_selectors:
                name_elem = item.select_one(selector)
                if name_elem:
                    name = name_elem.get_text(strip=True)
                    if name:
                        break
            
            if not name:
                return None
            
            price_selectors = [
                '[data-widget="searchResultsItem"] span[style*="color"]',
                '.tile-price span',
                '.price span'
            ]
            
            price = 0.0
            for selector in price_selectors:
                price_elem = item.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    price_match = re.search(r'(\d+(?:\s*\d+)*)', price_text.replace(' ', ''))
                    if price_match:
                        price = float(price_match.group(1))
                        break
            
            link_selectors = [
                'a[data-widget="searchResultsItem"]',
                '.tile-hover-target',
                'h3 a'
            ]
            
            product_url = ""
            product_id = ""
            for selector in link_selectors:
                link_elem = item.select_one(selector)
                if link_elem and link_elem.get('href'):
                    href = link_elem.get('href')
                    if href.startswith('/'):
                        product_url = f"{self.BASE_URL}{href}"
                    else:
                        product_url = href
                    
                    id_match = re.search(r'/product/[^/]*-(\d+)/', product_url)
                    if id_match:
                        product_id = id_match.group(1)
                        break
            
            if not product_id:
                product_id = f"ozon_{hash(name)}"
            
            img_elem = item.select_one('img')
            image_url = img_elem.get('src') if img_elem else None
            
            rating = 0.0
            
            return ProductInfo(
                marketplace="ozon",
                product_id=product_id,
                name=name,
                price=price,
                currency="RUB",
                url=product_url,
                image_url=image_url,
                rating=rating,
                reviews_count=0,
                availability=True
            )
            
        except Exception as e:
            logger.error(f"Error parsing search item: {e}")
            return None

    async def _parse_product_page(self, html: str, product_id: str) -> Optional[ProductInfo]:
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            name_selectors = [
                'h1[data-widget="webProductHeading"]',
                'h1',
                '[data-widget="webProductHeading"]'
            ]
            
            name = ""
            for selector in name_selectors:
                name_elem = soup.select_one(selector)
                if name_elem:
                    name = name_elem.get_text(strip=True)
                    if name:
                        break
            
            price_selectors = [
                '[data-widget="webPrice"] span',
                '.price span',
                'span[style*="color"]'
            ]
            
            price = 0.0
            for selector in price_selectors:
                price_elem = soup.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    price_match = re.search(r'(\d+(?:\s*\d+)*)', price_text.replace(' ', ''))
                    if price_match:
                        price = float(price_match.group(1))
                        break
            
            rating_elem = soup.select_one('[data-widget="webReviewProductScore"] span')
            rating = 0.0
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    rating = float(rating_match.group(1))
            
            return ProductInfo(
                marketplace="ozon",
                product_id=product_id,
                name=name,
                price=price,
                currency="RUB",
                url=f"{self.BASE_URL}/product/{product_id}/",
                rating=rating,
                availability=True
            )
            
        except Exception as e:
            logger.error(f"Error parsing product page: {e}")
            return None

    async def _get_product_from_cache(self, product_id: str) -> Optional[ProductInfo]:
        return None


def create_ozon_client(api_key: Optional[str] = None) -> OzonAPI:
    return OzonAPI(api_key) 