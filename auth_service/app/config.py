import os

class Settings:
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@db:5432/authdb")
    
    # JWT
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60
    
    # Kafka
    KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
    KAFKA_TOPIC_USER_EVENTS = "user-events"
    
    # App
    APP_NAME = "Auth Service"
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"

settings = Settings()