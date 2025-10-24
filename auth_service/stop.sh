#!/bin/bash

echo "⏹️  Stopping Auth Service..."

# Stop all containers but keep volumes
docker-compose down

echo "✅ All containers stopped. Data preserved in volumes."
echo ""
echo "📦 Existing volumes:"
docker volume ls | grep auth_service