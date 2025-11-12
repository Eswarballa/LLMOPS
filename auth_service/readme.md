# Auth Service Setup Guide

## 📁 Complete File Structure
```
auth_service/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── db.py
│   ├── utils.py
│   ├── kafka_producer.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── user_model.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth_routes.py
│   │   └── dashboard_routes.py
│   ├── static/
│   │   └── style.css
│   └── templates/
│       ├── login.html
│       └── dashboard.html
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## 🚀 Quick Start

### Step 1: Create Empty `__init__.py` Files
```bash
touch app/__init__.py
touch app/models/__init__.py
touch app/routes/__init__.py
```

### Step 2: Build and Start Services
```bash
# Stop any existing containers
docker-compose down -v

# Build and start all services
docker-compose up -d --build

# Check if all containers are running
docker ps
```

### Step 3: Verify Services
```bash
# Check auth service logs
docker logs auth_service_auth_service_1

# Check Kafka logs
docker logs auth_service_kafka_1

# Check database logs
docker logs auth_service_db_1
```
