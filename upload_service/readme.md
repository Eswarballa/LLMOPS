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

## 🧪 Testing the Upload Service

### Access the Upload Page

Open your browser: `http://localhost:8001/upload`

### Create a Test Model

Create a test model ZIP file:

```bash
# Create test model directory
mkdir -p test_model
cd test_model

# Create app.py
cat > app.py << 'EOF'
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    # Simple echo model
    return jsonify({
        'prediction': f"Processed: {data.get('input', 'no input')}",
        'model': 'test-model'
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
EOF

# Create requirements.txt
cat > requirements.txt << 'EOF'
flask==3.0.0
EOF

# Create ZIP
zip -r ../test_model.zip .
cd ..
```

### Upload via Web Interface

1. Go to `http://localhost:8001/upload`
2. Enter username: `testuser`
3. Enter model name: `test-model`
4. Enter description: `A simple test model`
5. Select `test_model.zip`
6. Click "Upload Model"

### Upload via API

```bash
curl -X POST http://localhost:8001/upload \
  -F "username=testuser" \
  -F "model_name=test-model" \
  -F "description=A simple test model" \
  -F "file=@test_model.zip"
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

## 🔍 Troubleshooting

### Docker Socket Permission Error

If you see "permission denied" when building Docker images:

```bash
# Give upload_service access to Docker socket
sudo chmod 666 /var/run/docker.sock

# Or add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

### Kafka Connection Issues

```bash
# Check Kafka is running
docker logs upload_service-kafka-1

# Restart Kafka
docker-compose restart kafka

# Wait 30 seconds then restart upload service
docker-compose restart upload_service
```

### Database Connection Error

```bash
# Check database
docker exec upload_service-db-1 pg_isready -U postgres

# View database logs
docker logs upload_service-db-1

# Recreate database
docker-compose down -v
docker-compose up -d
```

## 📦 Kafka Message Format

When a model is uploaded, the following message is published to `model-events` topic:

```json
{
  "event": "model.uploaded",
  "data": {
    "upload_id": 1,
    "username": "testuser",
    "model_name": "test-model",
    "description": "A simple test model",
    "docker_image": "ml-models/testuser/test-model:latest",
    "docker_container_id": "abc123def456...",
    "status": "ready"
  }
}
```

## 🔗 Integration with Auth Service

To integrate with the auth service:

1. Update auth service dashboard to link to upload service:

```html
<!-- In auth_service/app/templates/dashboard.html -->
<a href="http://localhost:8001/upload" class="btn btn-primary">
  Upload Model
</a>
```

2. Or create a combined docker-compose with both services:

```yaml
# Combined docker-compose.yml
version: "3.8"

services:
  # ... auth_service configuration ...
  
  upload_service:
    build: ./upload_service
    ports:
      - "8001:8001"
    environment:
      - AUTH_SERVICE_URL=http://auth_service:8000
    # ... rest of configuration ...

networks:
  shared_network:
    driver: bridge
```

## 🚀 Next Steps

1. **Inference Service**: Create a service that consumes `model-events` from Kafka and manages running containers
2. **Load Balancer**: Set up Nginx to route requests to appropriate services
3. **Authentication**: Add JWT token validation from auth service
4. **Model Registry**: Store Docker images in a private registry

## 📝 Notes

- Maximum upload size: 500MB (configurable in config.py)
- Docker images are tagged as: `ml-models/{username}/{model_name}:latest`
- Containers are created but not started automatically
- The inference service will start containers on-demand
- All uploaded files and extracted models are persisted in volumes

Good luck! 🎉