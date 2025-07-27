"""
Базовый API клиент для маркетплейсов
"""
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import re
import httpx
from fake_useragent import UserAgent

logger = logging.getLogger(__name__)


@dataclass
class ProductInfo:
    marketplace: str
    product_id: str
    name: str
    price: float
    currency: str
    url: str
    image_url: Optional[str] = None
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    availability: bool = True
    brand: Optional[str] = None
    seller: Optional[str] = None


class APIError(Exception):
    pass


class RateLimitError(APIError):
    pass


class ProductNotFoundError(APIError):
    pass


class ProductMatcher:
    @staticmethod
    def calculate_similarity(query: str, product_name: str) -> float:
        query_lower = query.lower().strip()
        product_lower = product_name.lower().strip()
        
        if query_lower == product_lower:
            return 1.0
        
        query_words = set(re.findall(r'\b\w+\b', query_lower))
        product_words = set(re.findall(r'\b\w+\b', product_lower))
        
        if not query_words or not product_words:
            return 0.0
        
        intersection = query_words.intersection(product_words)
        union = query_words.union(product_words)
        
        similarity = len(intersection) / len(union) if union else 0.0
        
        if ' '.join(query_words) in product_lower:
            similarity += 0.2
        
        len_diff = abs(len(query_lower) - len(product_lower))
        if len_diff > 50:
            similarity *= 0.8
        
        return min(similarity, 1.0)
    
    @staticmethod
    def find_best_match(query: str, products: List[ProductInfo]) -> Optional[ProductInfo]:
        if not products:
            return None
        
        best_product = None
        best_score = 0.0
        
        for product in products:
            if not product.name:
                continue
            
            score = ProductMatcher.calculate_similarity(query, product.name)
            
            if product.availability:
                score += 0.1
            
            if product.rating and product.rating >= 4.0:
                score += 0.05
            
            if product.reviews_count and product.reviews_count > 100:
                score += 0.05
            
            if product.price < 100:
                score -= 0.1
            
            if score > best_score:
                best_score = score
                best_product = product
        
        return best_product if best_score >= 0.3 else None


class BaseMarketplaceAPI(ABC):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.session: Optional[httpx.AsyncClient] = None
        self._user_agent = UserAgent()
        
    async def __aenter__(self):
        await self._init_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._close_session()
    
    async def _init_session(self):
        if not self.session:
            self.session = httpx.AsyncClient(
                timeout=30.0,
                headers={
                    'User-Agent': self._user_agent.random,
                    'Accept': 'application/json',
                    'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                }
            )
    
    async def _close_session(self):
        if self.session:
            await self.session.aclose()
            self.session = None
    
    async def _make_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        if not self.session:
            await self._init_session()
        
        try:
            response = await self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise RateLimitError(f"Rate limit exceeded for {url}")
            elif e.response.status_code == 404:
                raise ProductNotFoundError(f"Product not found: {url}")
            else:
                raise APIError(f"HTTP error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            raise APIError(f"Request failed: {str(e)}")
    
    @abstractmethod
    async def search_products(self, query: str, limit: int = 10) -> List[ProductInfo]:
        pass
    
    @abstractmethod
    async def get_product_by_id(self, product_id: str) -> Optional[ProductInfo]:
        pass
    
    async def get_product_price(self, product_id: str) -> Optional[float]:
        product = await self.get_product_by_id(product_id)
        return product.price if product else None
    
    async def find_best_product(self, query: str, limit: int = 10) -> Optional[ProductInfo]:
        try:
            products = await self.search_products(query, limit)
            return ProductMatcher.find_best_match(query, products)
        except Exception as e:
            logger.error(f"Error finding best product for '{query}': {e}")
            return None
    
    @property
    @abstractmethod
    def marketplace_name(self) -> str:
        pass 