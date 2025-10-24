from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
from .routes import upload_routes
from .db import init_db
from .services.kafka_service import kafka_service
from .config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("Starting Upload Service...")
    init_db()
    logger.info("Database initialized")
    
    await kafka_service.start()
    logger.info("Kafka producer started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Upload Service...")
    await kafka_service.stop()

app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

# Include routers
app.include_router(upload_routes.router, tags=["upload"])

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "upload_service"}

@app.get("/")
async def root():
    """Root endpoint"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/upload")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)