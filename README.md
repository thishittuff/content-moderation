# Content Moderation Service

A comprehensive AI-powered content moderation service built with FastAPI, OpenAI GPT-4, and modern async/await patterns. The service analyzes user-submitted text and images for inappropriate content, sends notifications via Slack and email, and provides analytics dashboards.

## 🚀 Features

- **AI-Powered Content Analysis**: Uses Google Gemini 1.5 Pro for text and Gemini 1.5 Pro Vision for image moderation
- **Multi-Content Support**: Handles both text and image content with intelligent classification
- **Real-time Notifications**: Sends alerts via Slack and email when inappropriate content is detected
- **Comprehensive Analytics**: Provides detailed user analytics and content moderation statistics
- **Error Tracking**: Integrated Sentry.io with automatic GitHub issue creation
- **Background Processing**: Celery-based task queue for handling image processing
- **Production Ready**: Docker containerization with PostgreSQL and Redis
- **Async Architecture**: Built with FastAPI and async/await patterns for high performance

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App  │    │   PostgreSQL    │    │     Redis      │
│                 │◄──►│   Database      │    │   Cache/Queue  │
│  - Text Mod.    │    │                 │    │                 │
│  - Image Mod.   │    │  - Requests     │    │  - Task Queue  │
│  - Analytics    │    │  - Results      │    │  - Caching     │
│  - Notifications│    │  - Logs         │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   OpenAI API    │    │   Slack API     │    │  BrevoMail API │
│                 │    │                 │    │                 │
│  - Gemini 1.5 Pro│    │  - Notifications│    │  - Email Alerts│
│  - Gemini Vision │    │  - Webhooks     │    │  - Templates   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🛠️ Technology Stack

- **Backend**: FastAPI with async/await patterns
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cache/Queue**: Redis with Celery
- **AI Integration**: Google Gemini 1.5 Pro and Gemini Vision
- **Notifications**: Slack API and BrevoMail API
- **Monitoring**: Sentry.io with GitHub integration
- **Containerization**: Docker with Docker Compose
- **Background Tasks**: Celery workers and beat scheduler

## 📋 Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Google API key
- Slack Bot Token (optional)
- BrevoMail API key (optional)
- Sentry DSN (optional)
- GitHub Personal Access Token (optional)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd content-moderation-service
```

### 2. Environment Configuration

Copy the environment template and configure your settings:

```bash
cp env.example .env
```

Edit `.env` file with your API keys and configuration:

```env
# Required
GOOGLE_API_KEY=your_google_api_key_here

# Optional but recommended
SLACK_BOT_TOKEN=your_slack_bot_token_here
SLACK_CHANNEL_ID=your_channel_id_here
BREVO_API_KEY=your_brevo_api_key_here
BREVO_SENDER_EMAIL=noreply@yourdomain.com
SENTRY_DSN=your_sentry_dsn_here
GITHUB_TOKEN=your_github_token_here
GITHUB_REPO=your_username/your_repo
```

### 3. Get Google API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the API key and paste it in your `.env` file
5. The service will use Gemini 1.5 Pro for text analysis and Gemini 1.5 Pro Vision for image analysis

### 4. Start Services with Docker

```bash
docker-compose up -d
```

This will start:
- PostgreSQL database (port 5432)
- Redis cache/queue (port 6379)
- FastAPI application (port 8000)
- Celery worker
- Celery beat scheduler
- Flower monitoring (port 5555)

### 5. Verify Installation

Check the health endpoint:

```bash
curl http://localhost:8000/api/v1/health
```

Access the API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📚 API Endpoints

### Text Moderation

```http
POST /api/v1/moderate/text
Content-Type: application/json

{
  "email_id": "user@example.com",
  "text_content": "Text content to moderate"
}
```

**Response:**
```json
{
  "id": 1,
  "email_id": "user@example.com",
  "content_type": "text",
  "status": "completed",
  "created_at": "2024-01-01T00:00:00Z",
  "result": {
    "id": 1,
    "classification": "safe",
    "confidence": 0.95,
    "reasoning": "Content appears to be appropriate",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

### Image Moderation

```http
POST /api/v1/moderate/image
Content-Type: application/json

{
  "email_id": "user@example.com",
  "image_data": "base64_encoded_image_data"
}
```

### Analytics

```http
GET /api/v1/analytics/summary?user=user@example.com
```

**Response:**
```json
{
  "user_email": "user@example.com",
  "total_requests": 15,
  "safe_content": 12,
  "inappropriate_content": 3,
  "pending_requests": 0,
  "recent_requests": [...]
}
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `GOOGLE_API_KEY` | Google API key for content analysis | Yes | - |
| `GEMINI_MODEL` | Gemini model to use | No | `gemini-2.5-flash-lite` |
| `DATABASE_URL` | PostgreSQL connection string | No | `postgresql+asyncpg://user:password@localhost:5432/content_moderation` |
| `REDIS_URL` | Redis connection string | No | `redis://localhost:6379/0` |
| `SLACK_BOT_TOKEN` | Slack bot token for notifications | No | - |
| `SLACK_CHANNEL_ID` | Slack channel ID for alerts | No | - |
| `BREVO_API_KEY` | BrevoMail API key for email | No | - |
| `BREVO_SENDER_EMAIL` | Sender email address | No | - |
| `SENTRY_DSN` | Sentry DSN for error tracking | No | - |
| `GITHUB_TOKEN` | GitHub token for issue creation | No | - |
| `GITHUB_REPO` | GitHub repository (owner/repo) | No | - |

### Content Classification

The service classifies content into five categories:

- **SAFE**: Appropriate content that follows community guidelines
- **TOXIC**: Harmful, offensive, or hate speech content
- **SPAM**: Unwanted promotional or repetitive content
- **HARASSMENT**: Content targeting individuals with abuse or threats
- **INAPPROPRIATE**: Content unsuitable for general audiences

## 🐳 Docker Commands

### Development

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up -d --build
```

### Production

```bash
# Build production image
docker build -t content-moderation:latest .

# Run production container
docker run -d \
  --name content-moderation \
  -p 8000:8000 \
  --env-file .env \
  content-moderation:latest
```

## 📊 Monitoring

### Health Checks

- **Application**: `GET /api/v1/health`
- **Database**: PostgreSQL health check in Docker Compose
- **Redis**: Redis health check in Docker Compose

### Celery Monitoring

- **Flower**: http://localhost:5555 (Celery task monitoring)
- **Worker Status**: Check Celery worker logs
- **Task Queue**: Monitor Redis queue status

### Sentry Integration

When configured, Sentry automatically:
- Captures all exceptions and errors
- Creates GitHub issues for critical errors
- Provides error tracking and performance monitoring

## 🔒 Security Features

- **Content Deduplication**: SHA-256 hashing prevents duplicate processing
- **Input Validation**: Pydantic models ensure data integrity
- **Error Handling**: Comprehensive error handling with Sentry integration
- **Environment Isolation**: Docker containers isolate services
- **API Rate Limiting**: Built-in FastAPI rate limiting capabilities

## 🧪 Testing

### Manual Testing

```bash
# Test text moderation
curl -X POST "http://localhost:8000/api/v1/moderate/text" \
  -H "Content-Type: application/json" \
  -d '{"email_id": "test@example.com", "text_content": "Hello world"}'

# Test analytics
curl "http://localhost:8000/api/v1/analytics/summary?user=test@example.com"
```

### Test Gemini Integration

```bash
# Test Gemini service directly
python test_gemini.py

# Run basic service tests
python test_service.py
```

### Automated Testing

```bash
# Run tests (when implemented)
pytest

# Run with coverage
pytest --cov=app
```

## 🚀 Deployment

### Production Considerations

1. **Environment Variables**: Use proper production values
2. **Database**: Use managed PostgreSQL service
3. **Redis**: Use managed Redis service
4. **Monitoring**: Enable Sentry and logging
5. **SSL/TLS**: Use reverse proxy (nginx) with SSL
6. **Scaling**: Use multiple Celery workers
7. **Backup**: Implement database backup strategy

### Kubernetes Deployment

```yaml
# Example Kubernetes deployment (not included)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: content-moderation
spec:
  replicas: 3
  selector:
    matchLabels:
      app: content-moderation
  template:
    metadata:
      labels:
        app: content-moderation
    spec:
      containers:
      - name: app
        image: content-moderation:latest
        ports:
        - containerPort: 8000
```

