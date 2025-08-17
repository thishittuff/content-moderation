#!/bin/bash

# Content Moderation Service Startup Script

echo "🚀 Starting Content Moderation Service..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from template..."
    if [ -f env.example ]; then
        cp env.example .env
        echo "✅ .env file created from template"
        echo "📝 Please edit .env file with your API keys before continuing"
        echo "   Required: GOOGLE_API_KEY"
        echo "   Optional: SLACK_BOT_TOKEN, BREVO_API_KEY, SENTRY_DSN, GITHUB_TOKEN"
        exit 1
    else
        echo "❌ env.example not found. Please create .env file manually"
        exit 1
    fi
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose and try again."
    exit 1
fi

echo "🔍 Checking environment configuration..."

# Check required environment variables
source .env

if [ -z "$GOOGLE_API_KEY" ] || [ "$GOOGLE_API_KEY" = "your_google_api_key_here" ]; then
    echo "❌ GOOGLE_API_KEY is required. Please set it in your .env file."
    exit 1
fi

echo "✅ Environment configuration looks good"

# Stop any existing containers
echo "🛑 Stopping any existing containers..."
docker-compose down

# Build and start services
echo "🏗️  Building and starting services..."
docker-compose up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo "🔍 Checking service health..."

# Check PostgreSQL
if docker-compose exec -T postgres pg_isready -U user -d content_moderation > /dev/null 2>&1; then
    echo "✅ PostgreSQL is ready"
else
    echo "❌ PostgreSQL is not ready"
fi

# Check Redis
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is ready"
else
    echo "❌ Redis is not ready"
fi

# Check FastAPI app
if curl -f http://localhost:8000/api/v1/health > /dev/null 2>&1; then
    echo "✅ FastAPI application is ready"
else
    echo "❌ FastAPI application is not ready"
fi

echo ""
echo "🎉 Content Moderation Service is starting up!"
echo ""
echo "📊 Service URLs:"
echo "   - API: http://localhost:8000"
echo "   - Documentation: http://localhost:8000/docs"
echo "   - Health Check: http://localhost:8000/api/v1/health"
echo "   - Celery Monitor: http://localhost:5555"
echo ""
echo "📝 Useful commands:"
echo "   - View logs: docker-compose logs -f app"
echo "   - Stop services: docker-compose down"
echo "   - Restart: docker-compose restart"
echo "   - Rebuild: docker-compose up -d --build"
echo ""
echo "🔍 Check logs for any startup issues:"
echo "   docker-compose logs -f"
