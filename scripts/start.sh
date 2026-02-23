#!/usr/bin/env bash

set -e

echo "🚀 Starting LuminaLib..."

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker compose down

# Build images
echo "🔨 Building Docker images..."
docker compose build

# Start services
echo "📦 Starting services..."
docker compose up -d

echo "⏳ Waiting for services to initialize..."
sleep 10

echo "📊 Current container status:"
docker compose ps

echo ""
echo "✅ LuminaLib is running!"
echo ""
echo "Swagger: http://localhost:8000/"
echo "RabbitMQ UI: http://localhost:15672 (guest/guest)"
echo ""
