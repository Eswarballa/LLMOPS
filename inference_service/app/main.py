from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging
import asyncio
from .routes import inference_routes
from .db import init_db, get_db
from .services.kafka_consumer import kafka_consumer
from .services.container_manager import container_manager
from .services.model_service import ModelService
from .config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Kafka event handler
async def handle_kafka_event(event: dict):
    """Handle incoming Kafka events"""
    try:
        event_type = event.get('event')
        
        if event_type == 'model.uploaded':
            logger.info(f"Received model.uploaded event: {event['data']['model_name']}")
            
            # Register model in database
            from .db import SessionLocal
            db = SessionLocal()
            try:
                ModelService.register_model(db, event['data'])
            finally:
                db.close()
        
        else:
            logger.info(f"Received unknown event type: {event_type}")
            
    except Exception as e:
        logger.error(f"Error handling Kafka event: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("Starting Inference Service...")
    init_db()
    logger.info("Database initialized")
    
    # Set Kafka callback
    kafka_consumer.set_callback(handle_kafka_event)
    await kafka_consumer.start()
    logger.info("Kafka consumer started")
    
    # Start container cleanup task
    asyncio.create_task(container_manager.cleanup_idle_containers())
    logger.info("Container cleanup task started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Inference Service...")
    await kafka_consumer.stop()

app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

# Include routers
app.include_router(inference_routes.router, tags=["inference"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)