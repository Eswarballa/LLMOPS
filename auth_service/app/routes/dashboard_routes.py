from fastapi import APIRouter, Depends, HTTPException, Request, Cookie
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
from ..db import get_db
from ..models.user_model import User
from ..utils import decode_access_token
from ..kafka_producer import kafka_producer
from ..config import settings

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def get_current_user(
    access_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
):
    """Verify JWT token and get current user"""
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    username = decode_access_token(access_token)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, user: User = Depends(get_current_user)):
    """Render dashboard page"""
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "username": user.username, "user_id": user.id}
    )

@router.post("/api/kafka/publish")
async def publish_kafka_event(
    request: Request,
    user: User = Depends(get_current_user)
):
    """Publish custom Kafka event from dashboard"""
    try:
        data = await request.json()
        event_type = data.get("event_type", "custom.event")
        message_data = data.get("data", {})
        
        # Add user context
        message = {
            "event": event_type,
            "user_id": user.id,
            "username": user.username,
            "data": message_data
        }
        
        # Send to Kafka
        success = await kafka_producer.send_message(
            settings.KAFKA_TOPIC_USER_EVENTS,
            message
        )
        
        if success:
            return JSONResponse({"status": "success", "message": "Event published to Kafka"})
        else:
            return JSONResponse(
                {"status": "error", "message": "Failed to publish event"},
                status_code=500
            )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/api/user/profile")
async def get_user_profile(user: User = Depends(get_current_user)):
    """Get current user profile"""
    return {
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "created_at": user.created_at.isoformat()
    }