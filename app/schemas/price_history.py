from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PriceHistoryBase(BaseModel):
    product_id: int
    marketplace: str
    price: float
    currency: str = "RUB"
    url: Optional[str] = None

class PriceHistoryCreate(PriceHistoryBase):
    pass

class PriceHistoryUpdate(BaseModel):
    price: Optional[float] = None
    currency: Optional[str] = None
    url: Optional[str] = None

class PriceHistory(PriceHistoryBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "product_id": 1,
                "marketplace": "amazon",
                "price": 1500.00,
                "currency": "RUB",
                "url": "https://amazon.com/product/123",
                "created_at": "2024-01-15T10:30:00"
            }
        }

class PriceHistoryList(BaseModel):
    items: list[PriceHistory]
    total: int
    page: int
    size: int

class PriceComparisonItem(BaseModel):
    marketplace: str
    current_price: float
    previous_price: Optional[float] = None
    price_change: Optional[float] = None
    price_change_percent: Optional[float] = None

class PriceComparison(BaseModel):
    product_id: int
    product_name: str
    comparison_date: datetime
    marketplaces: list[PriceComparisonItem]
    
    class Config:
        schema_extra = {
            "example": {
                "product_id": 1,
                "product_name": "iPhone 15",
                "comparison_date": "2024-01-15T10:30:00",
                "marketplaces": [
                    {
                        "marketplace": "amazon",
                        "current_price": 1500.00,
                        "previous_price": 1600.00,
                        "price_change": -100.00,
                        "price_change_percent": -6.25
                    }
                ]
            }
        }