#!/bin/bash

echo "⚠️  WARNING: This will delete ALL data including database!"
echo "Press Ctrl+C to cancel, or wait 5 seconds to continue..."
sleep 5

echo "🧹 Cleaning everything..."

# Stop and remove containers with volumes
docker-compose down -v

# Remove images
docker-compose rm -f

# Prune system
docker system prune -f

echo "✅ Complete cleanup done. All data removed."
echo ""
echo "To start fresh, run: ./start.sh"