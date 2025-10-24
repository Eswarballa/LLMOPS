import os
from sqlalchemy import create_engine, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables"""
    recreate = os.getenv("RECREATE_DB", "False").lower() == "true"
    
    if recreate:
        print("RECREATE_DB is True - Dropping and recreating all tables...")
        Base.metadata.drop_all(bind=engine)
    
    Base.metadata.create_all(bind=engine)
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"Database tables: {tables}")