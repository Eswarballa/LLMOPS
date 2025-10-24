#!/bin/bash

echo "🚀 Starting Auth Service..."

# Stop running containers without removing volumes
echo "⏹️  Stopping existing containers..."
docker-compose down

# Start database first
echo "🗄️  Starting PostgreSQL database..."
docker-compose up -d db

# Wait for database to be healthy
echo "⏳ Waiting for database to be ready..."
sleep 10

# Start Zookeeper and Kafka
echo "📨 Starting Kafka infrastructure..."
docker-compose up -d zookeeper

# Wait for Zookeeper
sleep 5

docker-compose up -d kafka

# Wait for Kafka to be ready
echo "⏳ Waiting for Kafka to be ready..."
sleep 25

# Start auth service
echo "🔐 Starting Auth Service..."
docker-compose up -d auth_service

# Wait a moment
sleep 5

# Show status
echo ""
echo "✅ Startup complete!"
echo ""
echo "📊 Container Status:"
docker-compose ps

echo ""
echo "🔍 Checking Auth Service logs..."
docker logs auth_service-auth_service-1 --tail 20

echo ""
echo "🌐 Application available at: http://localhost:8000"
echo "📊 Health check: http://localhost:8000/health"
echo ""
echo "📝 To view logs: docker logs -f auth_service-auth_service-1"