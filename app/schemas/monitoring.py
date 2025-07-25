from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class MonitoringRequest(BaseModel):
    product_name: str
    product_id: Optional[int] = None

class MonitoringResponse(BaseModel):
    task_id: str
    message: str
    product_name: str
    status: str = "started"

class TaskResultResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class MarketplaceRequest(BaseModel):
    product_name: str
    marketplace: str

    class Config:
        schema_extra = {
            "example": {
                "product_name": "Apple iPhone 13",
                "marketplace": "amazon"
            }
        }

class MarketplaceResponse(BaseModel):
    task_id: str
    message: str
    marketplace: str
    product_name: str
    product_name: str
    status: str = "started"

class PriceResult(BaseModel):
    marketplace: str
    product_name: str
    price: float
    currency: str
    timestamp: datetime
    url: Optional[str] = None

class ArbitrageAnalysis(BaseModel):
    min_price: float
    max_price: float

class MonitoringResult(BaseModel):
    product_name: str
    product_id: int
    prices: Dict[str, float]
    analysis: ArbitrageAnalysis
    timestamp: datetime

class TaskListResponse(BaseModel):
    active_tasks: Dict[str, Dict]
    total_count: int

class TestTaskResponse(BaseModel):
    task_id: str
    message: str
    status: str = "started"