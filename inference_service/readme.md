# Inference Service Setup Guide

## 📁 Complete File Structure

```
inference_service/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── db.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── model_registry.py
│   ├── routes/
│   │   ├── __init__.py
│   │   └── inference_routes.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── kafka_consumer.py
│   │   ├── container_manager.py
│   │   └── model_service.py
│   └── templates/
│       └── inference_dashboard.html
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## 🚀 Quick Start

### Step 1: Create Directory Structure

```bash
mkdir -p inference_service/app/{models,routes,services,templates}

# Create __init__.py files
touch inference_service/app/__init__.py
touch inference_service/app/models/__init__.py
touch inference_service/app/routes/__init__.py
touch inference_service/app/services/__init__.py
```

### Step 2: Create Shared Volume for Kafka Events

```bash
# Create a named volume that will be shared with upload_service
docker volume create upload_service_kafka_events
```

### Step 3: Build and Start

```bash
cd inference_service

# Fix Docker socket permissions
sudo chmod 666 /var/run/docker.sock

# Start service
docker-compose up -d --build

# Check logs
docker logs -f inference_service-inference_service-1
```

## 🔄 How It Works

### 1. **Event Consumption**
- Listens to Kafka events from upload service
- Automatically registers new models when uploaded
- Stores model metadata in PostgreSQL

### 2. **Container Management**
- Starts containers on-demand when inference is requested
- Manages multiple running containers simultaneously
- Automatically stops idle containers after timeout
- Maps each container's port 8080 to unique external ports

### 3. **Inference Flow**
```
User Request → Inference Service
              ↓
          Check if container running
              ↓ (No)
          Start container
              ↓
          Forward request to container
              ↓
          Return result to user
```

## 🧪 Testing

### Access Dashboard

Open: `http://localhost:8002`

You should see:
- All uploaded models
- Start/Stop buttons for each model
- Inference interface

### Test Workflow

1. **Upload a model** (from upload service):
   ```bash
   # Go to http://localhost:8001/upload
   # Upload your model ZIP
   ```

2. **Check inference dashboard**:
   ```bash
   # Go to http://localhost:8002
   # You should see your model listed
   ```

3. **Start a model**:
   - Click "▶️ Start" button
   - Container will start and port will be assigned

4. **Run inference**:
   - Enter JSON input in the text area
   - Click "🚀 Run Inference"
   - See results

### API Testing

```bash
# List all models
curl http://localhost:8002/api/models

# Get specific model
curl http://localhost:8002/api/models/1

# Start a model
curl -X POST http://localhost:8002/api/models/1/start

# Run inference
curl -X POST http://localhost:8002/api/models/1/infer \
  -H "Content-Type: application/json" \
  -d '{"input_data": {"input": "test"}}'

# Stop a model
curl -X POST http://localhost:8002/api/models/1/stop

# Get container stats
curl http://localhost:8002/api/stats
```

## ⚙️ Configuration

Edit `docker-compose.yml` to configure:

| Variable | Default | Description |
|----------|---------|-------------|
| MAX_RUNNING_CONTAINERS | 10 | Maximum simultaneous running containers |
| CONTAINER_IDLE_TIMEOUT | 300 | Seconds before stopping idle container |
| CONTAINER_STARTUP_TIMEOUT | 30 | Seconds to wait for container startup |

## 🔍 Monitoring

### Check Running Containers

```bash
# View stats via API
curl http://localhost:8002/api/stats

# Check Docker containers
docker ps | grep ml-models

# View inference service logs
docker logs -f inference_service-inference_service-1
```

### Container Lifecycle

The service automatically:
- ✅ Starts containers when inference is requested
- ✅ Keeps containers running while in use
- ✅ Stops containers after 5 minutes of inactivity
- ✅ Limits total running containers to prevent resource exhaustion

## 🐛 Troubleshooting

### Models Not Appearing

1. Check if upload service published event:
   ```bash
   docker exec -it upload_service_upload_service_1 cat /app/kafka_events.log
   ```

2. Check inference service logs:
   ```bash
   docker logs inference_service-inference_service-1 | grep "model.uploaded"
   ```

3. Manually check database:
   ```bash
   docker exec -it inference_service-db-1 psql -U postgres -d inferencedb
   SELECT * FROM model_registry;
   ```

### Container Won't Start

1. Check Docker socket permissions:
   ```bash
   ls -l /var/run/docker.sock
   # Should show: srw-rw-rw-
   ```

2. Check if container exists:
   ```bash
   docker ps -a | grep <container_name>
   ```

3. Try starting manually:
   ```bash
   docker start <container_id>
   ```

### Inference Request Fails

1. Check if container is running:
   ```bash
   docker ps | grep <model_name>
   ```

2. Check container logs:
   ```bash
   docker logs <container_id>
   ```

3. Test container directly:
   ```bash
   # Get port from dashboard or API
   curl -X POST http://localhost:<port>/predict \
     -H "Content-Type: application/json" \
     -d '{"input": "test"}'
   ```

## 📊 Architecture

```
┌─────────────────────────────────────────────┐
│  Inference Service (Port 8002)              │
│                                              │
│  ┌──────────────────────────────────────┐  │
│  │ Kafka Consumer                        │  │
│  │ (Listens to model.uploaded events)   │  │
│  └──────────────────────────────────────┘  │
│                                              │
│  ┌──────────────────────────────────────┐  │
│  │ Model Registry (PostgreSQL)           │  │
│  │ - Stores model metadata              │  │
│  │ - Tracks container status            │  │
│  └──────────────────────────────────────┘  │
│                                              │
│  ┌──────────────────────────────────────┐  │
│  │ Container Manager                     │  │
│  │ - Starts containers on demand         │  │
│  │ - Maps ports dynamically             │  │
│  │ - Stops idle containers              │  │
│  └──────────────────────────────────────┘  │
│                                              │
│  ┌──────────────────────────────────────┐  │
│  │ REST API                              │  │
│  │ - /api/models (list)                  │  │
│  │ - /api/models/{id}/start              │  │
│  │ - /api/models/{id}/infer              │  │
│  │ - /api/models/{id}/stop               │  │
│  └──────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
                    │
                    ↓
        ┌──────────────────────┐
        │  Model Containers     │
        │  (Port 8080 → Random) │
        │                       │
        │  User1/Model1: 32768  │
        │  User1/Model2: 32769  │
        │  User2/Model1: 32770  │
        └──────────────────────┘
```

## 🚀 Next Steps

1. **Add Authentication**: Integrate with auth service to validate users
2. **Add Load Balancing**: Use Nginx to distribute requests
3. **Add Monitoring**: Integrate Prometheus metrics
4. **Add Logging**: Centralized logging with ELK stack
5. **Add Caching**: Redis for frequently accessed models

Good luck! 🎉