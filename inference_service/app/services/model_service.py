from sqlalchemy.orm import Session
from ..models.model_registry import ModelRegistry
from typing import List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ModelService:
    
    @staticmethod
    def register_model(db: Session, model_data: dict) -> ModelRegistry:
        """Register a new model from Kafka event"""
        # Check if already registered
        existing = db.query(ModelRegistry).filter(
            ModelRegistry.upload_id == model_data['upload_id']
        ).first()
        
        if existing:
            logger.info(f"Model already registered: {existing.model_name}")
            return existing
        
        model = ModelRegistry(
            upload_id=model_data['upload_id'],
            username=model_data['username'],
            model_name=model_data['model_name'],
            description=model_data.get('description'),
            docker_image=model_data['docker_image'],
            docker_container_id=model_data['docker_container_id'],
            status='available'
        )
        
        db.add(model)
        db.commit()
        db.refresh(model)
        
        logger.info(f"Registered model: {model.model_name} (ID: {model.id})")
        return model
    
    @staticmethod
    def get_all_models(db: Session) -> List[ModelRegistry]:
        """Get all available models"""
        return db.query(ModelRegistry).all()
    
    @staticmethod
    def get_model_by_id(db: Session, model_id: int) -> Optional[ModelRegistry]:
        """Get model by ID"""
        return db.query(ModelRegistry).filter(ModelRegistry.id == model_id).first()
    
    @staticmethod
    def get_models_by_user(db: Session, username: str) -> List[ModelRegistry]:
        """Get all models for a user"""
        return db.query(ModelRegistry).filter(ModelRegistry.username == username).all()
    
    @staticmethod
    def update_model_status(
        db: Session, 
        model_id: int, 
        status: str, 
        external_port: Optional[int] = None
    ):
        """Update model status"""
        model = db.query(ModelRegistry).filter(ModelRegistry.id == model_id).first()
        if model:
            model.status = status
            if external_port is not None:
                model.external_port = external_port
            if status == 'running':
                model.last_used = datetime.utcnow()
            db.commit()
            logger.info(f"Updated model {model_id} status to {status}")
    
    @staticmethod
    def delete_model(db: Session, model_id: int):
        """Delete model from registry"""
        model = db.query(ModelRegistry).filter(ModelRegistry.id == model_id).first()
        if model:
            db.delete(model)
            db.commit()
            logger.info(f"Deleted model: {model_id}")