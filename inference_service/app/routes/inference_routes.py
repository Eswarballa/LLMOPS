from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import requests
import time
import logging

from ..db import get_db
from ..services.model_service import ModelService
from ..services.container_manager import container_manager
from ..models.model_registry import ModelInfo, InferenceRequest, InferenceResponse

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    """Render inference dashboard with all available models"""
    models = ModelService.get_all_models(db)
    return templates.TemplateResponse(
        "inference_dashboard.html",
        {"request": request, "models": models}
    )

@router.get("/api/models")
async def list_models(db: Session = Depends(get_db)):
    """Get list of all available models"""
    models = ModelService.get_all_models(db)
    return {"models": [ModelInfo.from_orm(m) for m in models]}

@router.get("/api/models/{model_id}")
async def get_model(model_id: int, db: Session = Depends(get_db)):
    """Get specific model details"""
    model = ModelService.get_model_by_id(db, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return ModelInfo.from_orm(model)

@router.post("/api/models/{model_id}/start")
async def start_model(model_id: int, db: Session = Depends(get_db)):
    """Start a model container"""
    model = ModelService.get_model_by_id(db, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    try:
        # Start container
        external_port = container_manager.start_container(model.docker_container_id, model_id)
        
        # Update status
        ModelService.update_model_status(db, model_id, "running", external_port)
        
        return {
            "status": "success",
            "message": "Model container started",
            "model_id": model_id,
            "external_port": external_port
        }
    except Exception as e:
        logger.error(f"Failed to start model {model_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start container: {str(e)}")

@router.post("/api/models/{model_id}/stop")
async def stop_model(model_id: int, db: Session = Depends(get_db)):
    """Stop a model container"""
    model = ModelService.get_model_by_id(db, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    try:
        container_manager.stop_container(model.docker_container_id)
        ModelService.update_model_status(db, model_id, "available", None)
        
        return {
            "status": "success",
            "message": "Model container stopped",
            "model_id": model_id
        }
    except Exception as e:
        logger.error(f"Failed to stop model {model_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop container: {str(e)}")

@router.post("/api/models/{model_id}/infer", response_model=InferenceResponse)
async def run_inference(
    model_id: int,
    request_data: InferenceRequest,
    db: Session = Depends(get_db)
):
    """
    Run inference on a model
    - Starts container if not running
    - Sends request to model's API
    - Returns inference result
    """
    model = ModelService.get_model_by_id(db, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    start_time = time.time()
    
    try:
        # Check if container is running
        external_port = container_manager.get_container_port(model.docker_container_id)
        
        # Start container if not running
        if not external_port:
            logger.info(f"Starting container for model {model_id}...")
            external_port = container_manager.start_container(model.docker_container_id, model_id)
            ModelService.update_model_status(db, model_id, "running", external_port)
            
            # Wait a bit for container to be ready
            time.sleep(3)
        
        # Make inference request to the model container
        model_url = f"http://localhost:{external_port}/predict"
        logger.info(f"Sending inference request to {model_url}")
        
        response = requests.post(
            model_url,
            json=request_data.input_data,
            timeout=30
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Model returned error: {response.text}"
            )
        
        result = response.json()
        inference_time = time.time() - start_time
        
        # Update last used time
        ModelService.update_model_status(db, model_id, "running", external_port)
        
        return InferenceResponse(
            model_id=model_id,
            model_name=model.model_name,
            result=result,
            inference_time=inference_time,
            status="success"
        )
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Inference request failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Model unavailable or not responding: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Inference failed: {e}")
        raise HTTPException(status_code=500, detail=f"Inference failed: {str(e)}")

@router.get("/api/stats")
async def get_stats():
    """Get container manager statistics"""
    return container_manager.get_stats()

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "inference_service"}