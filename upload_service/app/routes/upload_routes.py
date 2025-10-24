from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
import logging

from ..db import get_db
from ..services.storage_service import StorageService
from ..services.docker_service import docker_service
from ..services.kafka_service import kafka_service
from ..services.metadata_service import MetadataService
from ..models.upload_model import ModelUploadResponse

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    """Render upload page"""
    return templates.TemplateResponse("upload.html", {"request": request})

@router.post("/upload")
async def upload_model(
    username: str = Form(...),
    model_name: str = Form(...),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload model, build Docker image, and publish to Kafka
    """
    try:
        logger.info(f"Received upload request: {model_name} from {username}")
        
        # Validate file type
        if not file.filename.endswith('.zip'):
            raise HTTPException(status_code=400, detail="Only .zip files are allowed")
        
        # Check if model already exists
        existing = MetadataService.get_upload_by_name(db, username, model_name)
        if existing:
            raise HTTPException(status_code=400, detail="Model with this name already exists")
        
        # Step 1: Save and extract zip file
        logger.info("Step 1: Saving and extracting zip file...")
        zip_path, extracted_path = await StorageService.save_upload(file, username, model_name)
        
        # Step 2: Build Docker image
        logger.info("Step 2: Building Docker image...")
        try:
            docker_image = docker_service.build_image(extracted_path, username, model_name)
        except Exception as e:
            StorageService.cleanup_model(username, model_name)
            raise HTTPException(status_code=500, detail=f"Docker build failed: {str(e)}")
        
        # Step 3: Create container (don't start it)
        logger.info("Step 3: Creating Docker container...")
        container_name = f"{username}_{model_name}".replace(" ", "_").lower()
        try:
            container_info = docker_service.create_container(docker_image, container_name)
            container_id = container_info['container_id']
        except Exception as e:
            docker_service.remove_image(docker_image)
            StorageService.cleanup_model(username, model_name)
            raise HTTPException(status_code=500, detail=f"Container creation failed: {str(e)}")
        
        # Step 4: Save metadata to database
        logger.info("Step 4: Saving metadata to database...")
        upload_record = MetadataService.create_upload_record(
            db=db,
            username=username,
            model_name=model_name,
            description=description,
            file_path=zip_path,
            extracted_path=extracted_path,
            docker_image=docker_image,
            docker_container_id=container_id
        )
        
        # Update status to ready
        MetadataService.update_status(db, upload_record.id, "ready", container_id)
        
        # Step 5: Publish to Kafka
        logger.info("Step 5: Publishing to Kafka...")
        kafka_message = {
            "upload_id": upload_record.id,
            "username": username,
            "model_name": model_name,
            "description": description,
            "docker_image": docker_image,
            "docker_container_id": container_id,
            "status": "ready"
        }
        await kafka_service.publish_model_uploaded(kafka_message)
        
        logger.info(f"Upload completed successfully: {model_name}")
        
        return JSONResponse({
            "status": "success",
            "message": "Model uploaded successfully",
            "data": {
                "upload_id": upload_record.id,
                "model_name": model_name,
                "docker_image": docker_image,
                "docker_container_id": container_id
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/models/{username}")
async def get_user_models(username: str, db: Session = Depends(get_db)):
    """Get all models uploaded by a user"""
    models = MetadataService.get_user_uploads(db, username)
    return {"models": [ModelUploadResponse.from_orm(m) for m in models]}

@router.get("/models/{username}/{model_name}")
async def get_model_details(username: str, model_name: str, db: Session = Depends(get_db)):
    """Get details of a specific model"""
    model = MetadataService.get_upload_by_name(db, username, model_name)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return ModelUploadResponse.from_orm(model)

@router.delete("/models/{upload_id}")
async def delete_model(upload_id: int, db: Session = Depends(get_db)):
    """Delete a model"""
    upload = MetadataService.get_upload_by_id(db, upload_id)
    if not upload:
        raise HTTPException(status_code=404, detail="Model not found")
    
    # Cleanup storage
    StorageService.cleanup_model(upload.username, upload.model_name)
    
    # Remove Docker image
    docker_service.remove_image(upload.docker_image)
    
    # Delete from database
    MetadataService.delete_upload(db, upload_id)
    
    return {"message": "Model deleted successfully"}