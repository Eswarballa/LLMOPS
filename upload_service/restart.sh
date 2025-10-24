#!/bin/bash

echo "🔄 Restarting Auth Service (preserving data)..."

# Restart all services
docker-compose restart

echo "✅ Services restarted!"
echo ""
echo "📊 Container Status:"
docker-compose ps

echo ""
echo "🌐 Application available at: http://localhost:8000"