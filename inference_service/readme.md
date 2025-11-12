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

### Container Lifecycle

The service automatically:
- ✅ Starts containers when inference is requested
- ✅ Keeps containers running while in use
- ✅ Stops containers after 5 minutes of inactivity
- ✅ Limits total running containers to prevent resource exhaustion

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
