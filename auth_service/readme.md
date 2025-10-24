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

## 🧪 Testing the Service

### Access the Application
Open your browser and go to: `http://localhost:8000`

### Test Registration
1. Click on "Register" tab
2. Enter username: `testuser`
3. Enter password: `test123`
4. Click Register
5. You should see "Registration successful! Please login."

### Test Login
1. Enter username: `testuser`
2. Enter password: `test123`
3. Click Login
4. You should be redirected to the dashboard

### Test Kafka Event Publishing
1. On the dashboard, select an event type
2. Modify the JSON data if needed
3. Click "Publish to Kafka"
4. Check the activity log for confirmation

## 🔍 Troubleshooting

### Container Exits Immediately
```bash
# Check logs for specific container
docker logs <container_name>

# Common issues:
# 1. Missing python-multipart (already added to requirements.txt)
# 2. Kafka connection issues (wait for kafka to fully start)
# 3. Database connection issues (check DATABASE_URL)
```

### Kafka Won't Start
```bash
# Make sure Zookeeper is running first
docker ps | grep zookeeper

# Restart Kafka
docker-compose restart kafka

# Check Kafka logs
docker logs auth_service_kafka_1 --tail 100
```

### Database Connection Error
```bash
# Check if database is ready
docker exec auth_service_db_1 pg_isready -U postgres

# Access database shell
docker exec -it auth_service_db_1 psql -U postgres -d authdb

# List tables
\dt

# Check users table
SELECT * FROM users;
```

## 📊 Monitoring Kafka Events

### Install Kafka CLI tools (optional)
```bash
# Enter Kafka container
docker exec -it auth_service_kafka_1 bash

# List topics
kafka-topics.sh --list --bootstrap-server localhost:9092

# Consume messages from user-events topic
kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic user-events \
  --from-beginning
```

## 🔧 Environment Variables

You can customize these in `docker-compose.yml`:

| Variable | Default | Description |
|----------|---------|-------------|
| DATABASE_URL | postgresql://postgres:password@db:5432/authdb | PostgreSQL connection string |
| KAFKA_BROKER | kafka:9092 | Kafka broker address |
| SECRET_KEY | your-super-secret-key-change-in-production | JWT secret key |
| DEBUG | True | Enable debug mode |

## 🌐 API Endpoints

### Public Endpoints
- `GET /` - Login page
- `POST /register` - Register new user
- `POST /login` - Login and get JWT token
- `GET /health` - Health check endpoint

### Protected Endpoints (require authentication)
- `GET /dashboard` - User dashboard
- `GET /api/user/profile` - Get user profile
- `POST /api/kafka/publish` - Publish event to Kafka
- `GET /logout` - Logout user

## 🎯 Next Steps

After the auth service is working:
1. Create upload service (VM2)
2. Create inference service (VM3)
3. Set up load balancer (VM4)
4. Deploy to OpenStack VMs

## 📝 Notes

- All containers restart automatically on failure (`restart: unless-stopped`)
- Database data is persisted in Docker volume `db_data`
- Kafka creates `user-events` topic automatically on startup
- JWT tokens expire after 60 minutes (configurable in config.py)



## ✅ Success Checklist

- [ ] All 4 containers are running (`docker ps` shows 4 containers)
- [ ] Login page loads at `http://localhost:8000`
- [ ] Can register a new user
- [ ] Can login with registered user
- [ ] Dashboard loads after login
- [ ] Can publish Kafka events from dashboard
- [ ] Can see Kafka messages in logs

## 🚀 Production Deployment (OpenStack)

When ready to deploy to VMs:
1. Push Docker images to Docker Hub or private registry
2. SSH into VM1 (auth server)
3. Pull docker-compose.yml
4. Update environment variables (especially SECRET_KEY)
5. Run `docker-compose up -d`
6. Configure firewall to allow port 8000
7. Set up reverse proxy (nginx) for HTTPS

Good luck with your deployment! 🎉