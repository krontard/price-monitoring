from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    amazon_url: Optional[HttpUrl] = None
    wildberries_url: Optional[HttpUrl] = None
    ozon_url: Optional[HttpUrl] = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(ProductBase):
    name: Optional[str] = None
    description: Optional[str] = None
    amazon_url: Optional[HttpUrl] = None
    wildberries_url: Optional[HttpUrl] = None
    ozon_url: Optional[HttpUrl] = None

class Product(ProductBase):
    id: int
    user_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True