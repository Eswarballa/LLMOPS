from sqlalchemy import Column, Integer, String, DateTime, Boolean
from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from ..db import Base

# SQLAlchemy Model
class ModelRegistry(Base):
    __tablename__ = "model_registry"
    
    id = Column(Integer, primary_key=True, index=True)
    upload_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String, nullable=False, index=True)
    model_name = Column(String, nullable=False, index=True)
    description = Column(String, nullable=True)
    docker_image = Column(String, nullable=False)
    docker_container_id = Column(String, nullable=False)
    status = Column(String, default="available")  # available, running, stopped, failed
    external_port = Column(Integer, nullable=True)  # Port when running
    last_used = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<ModelRegistry(id={self.id}, model_name={self.model_name}, status={self.status})>"

# Pydantic Schemas
class ModelInfo(BaseModel):
    id: int
    upload_id: int
    username: str
    model_name: str
    description: Optional[str]
    docker_image: str
    docker_container_id: str
    status: str
    external_port: Optional[int]
    last_used: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

class InferenceRequest(BaseModel):
    input_data: dict

class InferenceResponse(BaseModel):
    model_id: int
    model_name: str
    result: dict
    inference_time: float
    status: str