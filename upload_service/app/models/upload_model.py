from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from ..db import Base

# SQLAlchemy Model
class ModelUpload(Base):
    __tablename__ = "model_uploads"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False, index=True)
    model_name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    file_path = Column(String, nullable=False)
    extracted_path = Column(String, nullable=False)
    docker_image = Column(String, nullable=False)
    docker_container_id = Column(String, nullable=True)
    status = Column(String, default="uploaded")  # uploaded, building, ready, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<ModelUpload(id={self.id}, model_name={self.model_name}, status={self.status})>"

# Pydantic Schemas
class ModelUploadCreate(BaseModel):
    username: str
    model_name: str
    description: Optional[str] = None

class ModelUploadResponse(BaseModel):
    id: int
    username: str
    model_name: str
    description: Optional[str]
    docker_image: str
    docker_container_id: Optional[str]
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True