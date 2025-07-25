from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text, nullable=True)
    amazon_url = Column(String, nullable=True)
    wildberries_url = Column(String, nullable=True)
    ozon_url = Column(String, nullable=True)

    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=func.now())

    user = relationship("User", back_populates="products")
    price_history = relationship("PriceHistory", back_populates="product")
    tasks = relationship("TaskHistory", back_populates="product")