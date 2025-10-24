from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
from .routes import auth_routes, dashboard_routes
from .db import init_db
from .kafka_producer import kafka_producer
from .config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("Starting Auth Service...")
    init_db()
    logger.info("Database initialized")
    
    await kafka_producer.start()
    logger.info("Kafka producer started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Auth Service...")
    await kafka_producer.stop()

app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include routers
app.include_router(auth_routes.router, tags=["auth"])
app.include_router(dashboard_routes.router, tags=["dashboard"])

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "auth_service"}

@app.get("/")
async def root():
    """Root endpoint - redirects to login"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)