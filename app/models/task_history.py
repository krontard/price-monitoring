from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class TaskHistory(Base):
    __tablename__ = "task_history"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String, unique=True, index=True)  # Celery task ID
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    product_name = Column(String)
    status = Column(String)  # started, pending, completed, failed, stopped
    error_message = Column(Text, nullable=True)
    result_data = Column(Text, nullable=True)  # JSON результат
    started_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime, nullable=True)
    
    product = relationship("Product", back_populates="tasks")