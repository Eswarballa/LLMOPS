import os

class Settings:
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@db:5432/inferencedb")
    
    # Kafka
    KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
    KAFKA_TOPIC_MODEL_EVENTS = "model-events"
    KAFKA_GROUP_ID = "inference-service"
    
    # Docker
    DOCKER_HOST = os.getenv("DOCKER_HOST", "unix://var/run/docker.sock")
    
    # Container Management
    MAX_RUNNING_CONTAINERS = int(os.getenv("MAX_RUNNING_CONTAINERS", "10"))
    CONTAINER_IDLE_TIMEOUT = int(os.getenv("CONTAINER_IDLE_TIMEOUT", "300"))  # 5 minutes
    CONTAINER_STARTUP_TIMEOUT = int(os.getenv("CONTAINER_STARTUP_TIMEOUT", "30"))  # 30 seconds
    
    # App
    APP_NAME = "Inference Service"
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # Upload Service (for fetching model metadata)
    UPLOAD_SERVICE_URL = os.getenv("UPLOAD_SERVICE_URL", "http://upload_service:8001")

settings = Settings()