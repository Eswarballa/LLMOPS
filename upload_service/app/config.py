import os

class Settings:
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@db:5432/uploaddb")
    
    # Kafka
    KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
    KAFKA_TOPIC_MODEL_EVENTS = "model-events"
    
    # Storage
    UPLOAD_DIR = "/app/uploads"
    MODELS_DIR = "/app/models"
    MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
    
    # Docker
    DOCKER_REGISTRY = os.getenv("DOCKER_REGISTRY", "localhost:5000")
    DOCKER_IMAGE_PREFIX = os.getenv("DOCKER_IMAGE_PREFIX", "ml-models")
    
    # App
    APP_NAME = "Upload Service"
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # Auth Service
    AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth_service:8000")

settings = Settings()

# Create directories if they don't exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.MODELS_DIR, exist_ok=True)