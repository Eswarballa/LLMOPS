from fastapi import APIRouter, Depends, HTTPException, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from ..db import get_db
from ..models.user_model import User
from ..utils import hash_password, verify_password, create_access_token
from ..kafka_producer import kafka_producer
from ..config import settings

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    """Render login page"""
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/register")
async def register(
    username: str = Form(...), 
    password: str = Form(...),
    email: str = Form(None),
    db: Session = Depends(get_db)
):
    """Register new user"""
    # Check if user exists
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Create new user
    hashed_pwd = hash_password(password)
    new_user = User(username=username, hashed_password=hashed_pwd, email=email)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Send Kafka event
    await kafka_producer.send_message(
        settings.KAFKA_TOPIC_USER_EVENTS,
        {
            "event": "user.registered",
            "user_id": new_user.id,
            "username": new_user.username,
            "timestamp": new_user.created_at.isoformat()
        }
    )
    
    return {"message": "User registered successfully", "user_id": new_user.id}

@router.post("/login")
async def login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Login user and return JWT token"""
    # Find user
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create JWT token
    token = create_access_token(data={"sub": user.username, "user_id": user.id})
    
    # Send Kafka event
    await kafka_producer.send_message(
        settings.KAFKA_TOPIC_USER_EVENTS,
        {
            "event": "user.login",
            "user_id": user.id,
            "username": user.username,
            "timestamp": str(user.created_at)
        }
    )
    
    # Redirect to dashboard with token as cookie
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(key="access_token", value=token, httponly=True)
    return response

@router.get("/logout")
async def logout():
    """Logout user by clearing token"""
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("access_token")
    return response