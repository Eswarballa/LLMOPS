# Upload Service Setup Guide

## 📁 Complete File Structure

```
upload_service/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── db.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── upload_model.py
│   ├── routes/
│   │   ├── __init__.py
│   │   └── upload_routes.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── storage_service.py
│   │   ├── docker_service.py
│   │   ├── kafka_service.py
│   │   └── metadata_service.py
│   └── templates/
│       └── upload.html
├── uploads/          # Will be created automatically
├── models/           # Will be created automatically
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## 🚀 Quick Start

### Step 1: Create Directory Structure

```bash
mkdir -p upload_service/app/{models,routes,services,templates}
mkdir -p upload_service/uploads
mkdir -p upload_service/models

# Create __init__.py files
touch upload_service/app/__init__.py
touch upload_service/app/models/__init__.py
touch upload_service/app/routes/__init__.py
touch upload_service/app/services/__init__.py
```

### Step 2: Build and Start

```bash
cd upload_service

# Start all services
docker-compose up -d --build

# Check logs
docker logs upload_service-upload_service-1 -f
```

### Step 3: Verify Services

```bash
# Check all containers
docker ps

# You should see:
# - upload_service-upload_service-1 (port 8001)
# - upload_service-db-1 (port 5433)
# - upload_service-kafka-1 (port 9092)
# - upload_service-zookeeper-1 (port 2181)
```

## 📊 API Endpoints

### Upload Model
```
POST /upload
Content-Type: multipart/form-data

Fields:
- username (string, required)
- model_name (string, required)
- description (string, optional)
- file (file, required, .zip)
```

### Get User Models
```
GET /models/{username}

Response:
{
  "models": [
    {
      "id": 1,
      "username": "testuser",
      "model_name": "test-model",
      "docker_image": "ml-models/testuser/test-model:latest",
      "docker_container_id": "abc123...",
      "status": "ready",
      "created_at": "2025-01-01T00:00:00"
    }
  ]
}
```

### Get Model Details
```
GET /models/{username}/{model_name}
```

### Delete Model
```
DELETE /models/{upload_id}
```

### Health Check
```
GET /health

Response:
{
  "status": "healthy",
  "service": "upload_service"
}
```
