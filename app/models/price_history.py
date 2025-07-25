from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    price = Column(Float)
    marketplace = Column(String)
    currency = Column(String, default="RUB")
    created_at = Column(DateTime, default=func.now())
    
    product = relationship("Product", back_populates="price_history")