from sqlalchemy.orm import Session
from ..models.upload_model import ModelUpload
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class MetadataService:
    
    @staticmethod
    def create_upload_record(
        db: Session,
        username: str,
        model_name: str,
        description: Optional[str],
        file_path: str,
        extracted_path: str,
        docker_image: str,
        docker_container_id: Optional[str] = None
    ) -> ModelUpload:
        """Create a new model upload record"""
        upload = ModelUpload(
            username=username,
            model_name=model_name,
            description=description,
            file_path=file_path,
            extracted_path=extracted_path,
            docker_image=docker_image,
            docker_container_id=docker_container_id,
            status="building"
        )
        db.add(upload)
        db.commit()
        db.refresh(upload)
        logger.info(f"Created upload record: {upload.id}")
        return upload
    
    @staticmethod
    def update_status(db: Session, upload_id: int, status: str, container_id: Optional[str] = None):
        """Update upload status"""
        upload = db.query(ModelUpload).filter(ModelUpload.id == upload_id).first()
        if upload:
            upload.status = status
            if container_id:
                upload.docker_container_id = container_id
            db.commit()
            logger.info(f"Updated upload {upload_id} status to {status}")
    
    @staticmethod
    def get_user_uploads(db: Session, username: str) -> List[ModelUpload]:
        """Get all uploads for a user"""
        return db.query(ModelUpload).filter(ModelUpload.username == username).all()
    
    @staticmethod
    def get_upload_by_id(db: Session, upload_id: int) -> Optional[ModelUpload]:
        """Get upload by ID"""
        return db.query(ModelUpload).filter(ModelUpload.id == upload_id).first()
    
    @staticmethod
    def get_upload_by_name(db: Session, username: str, model_name: str) -> Optional[ModelUpload]:
        """Get upload by username and model name"""
        return db.query(ModelUpload).filter(
            ModelUpload.username == username,
            ModelUpload.model_name == model_name
        ).first()
    
    @staticmethod
    def delete_upload(db: Session, upload_id: int):
        """Delete upload record"""
        upload = db.query(ModelUpload).filter(ModelUpload.id == upload_id).first()
        if upload:
            db.delete(upload)
            db.commit()
            logger.info(f"Deleted upload record: {upload_id}")