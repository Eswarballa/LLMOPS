#!/bin/bash

echo "🚀 Starting Inference Service..."

# Fix Docker socket permissions
echo "🔧 Setting Docker socket permissions..."
sudo chmod 666 /var/run/docker.sock

# Create shared volume if it doesn't exist
echo "📦 Creating shared volume for Kafka events..."
docker volume create upload_service_kafka_events 2>/dev/null || true

# Stop running containers without removing volumes
echo "⏹️  Stopping existing containers..."
docker-compose down

# Start database first
echo "🗄️  Starting PostgreSQL database..."
docker-compose up -d db

# Wait for database to be healthy
echo "⏳ Waiting for database to be ready..."
sleep 10

# Start inference service
echo "🤖 Starting Inference Service..."
docker-compose up -d inference_service

# Wait a moment
sleep 5

# Show status
echo ""
echo "✅ Startup complete!"
echo ""
echo "📊 Container Status:"
docker-compose ps

echo ""
echo "🔍 Checking Inference Service logs..."
docker logs inference_service-inference_service-1 --tail 20

echo ""
echo "🌐 Application available at: http://localhost:8002"
echo "📊 Health check: http://localhost:8002/health"
echo ""
echo "📝 To view logs: docker logs -f inference_service-inference_service-1"
echo ""
echo "⚠️  Make sure upload service is running to receive model events!"