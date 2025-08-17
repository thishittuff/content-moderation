@echo off
REM Content Moderation Service Startup Script for Windows

echo 🚀 Starting Content Moderation Service...

REM Check if .env file exists
if not exist .env (
    echo ⚠️  .env file not found. Creating from template...
    if exist env.example (
        copy env.example .env
        echo ✅ .env file created from template
        echo 📝 Please edit .env file with your API keys before continuing
        echo    Required: GOOGLE_API_KEY
        echo    Optional: SLACK_BOT_TOKEN, BREVO_API_KEY, SENTRY_DSN, GITHUB_TOKEN
        pause
        exit /b 1
    ) else (
        echo ❌ env.example not found. Please create .env file manually
        pause
        exit /b 1
    )
)

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not running. Please start Docker and try again.
    pause
    exit /b 1
)

REM Check if Docker Compose is available
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose is not installed. Please install Docker Compose and try again.
    pause
    exit /b 1
)

echo 🔍 Checking environment configuration...

REM Check required environment variables
for /f "tokens=1,2 delims==" %%a in (.env) do (
    if "%%a"=="GOOGLE_API_KEY" (
        if "%%b"=="your_google_api_key_here" (
            echo ❌ GOOGLE_API_KEY is required. Please set it in your .env file.
            pause
            exit /b 1
        )
    )
)

echo ✅ Environment configuration looks good

REM Stop any existing containers
echo 🛑 Stopping any existing containers...
docker-compose down

REM Build and start services
echo 🏗️  Building and starting services...
docker-compose up -d --build

REM Wait for services to be ready
echo ⏳ Waiting for services to be ready...
timeout /t 10 /nobreak >nul

REM Check service health
echo 🔍 Checking service health...

REM Check PostgreSQL
docker-compose exec -T postgres pg_isready -U user -d content_moderation >nul 2>&1
if errorlevel 1 (
    echo ❌ PostgreSQL is not ready
) else (
    echo ✅ PostgreSQL is ready
)

REM Check Redis
docker-compose exec -T redis redis-cli ping >nul 2>&1
if errorlevel 1 (
    echo ❌ Redis is not ready
) else (
    echo ✅ Redis is ready
)

REM Check FastAPI app
curl -f http://localhost:8000/api/v1/health >nul 2>&1
if errorlevel 1 (
    echo ❌ FastAPI application is not ready
) else (
    echo ✅ FastAPI application is ready
)

echo.
echo 🎉 Content Moderation Service is starting up!
echo.
echo 📊 Service URLs:
echo    - API: http://localhost:8000
echo    - Documentation: http://localhost:8000/docs
echo    - Health Check: http://localhost:8000/api/v1/health
echo    - Celery Monitor: http://localhost:5555
echo.
echo 📝 Useful commands:
echo    - View logs: docker-compose logs -f app
echo    - Stop services: docker-compose down
echo    - Restart: docker-compose restart
echo    - Rebuild: docker-compose up -d --build
echo.
echo 🔍 Check logs for any startup issues:
echo    docker-compose logs -f
echo.
pause
