# AI Platform Backend

## Quick Start

### Using Docker Compose

```bash
cd ai-platform
docker-compose up -d
```

### Local Development

1. Create a virtual environment:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Start PostgreSQL and Redis (or use Docker):
```bash
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:15
docker run -d -p 6379:6379 redis:7
```

5. Run the application:
```bash
uvicorn app.main:app --reload
```

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| DATABASE_URL | PostgreSQL connection string | postgresql+asyncpg://postgres:postgres@localhost:5432/aiplatform |
| REDIS_URL | Redis connection string | redis://localhost:6379/0 |
| OLLAMA_BASE_URL | Ollama server URL | http://localhost:11434 |
| OLLAMA_DEFAULT_MODEL | Default Ollama model | llama2 |
| OPENAI_API_KEY | OpenAI API key | - |
| OPENAI_API_BASE | OpenAI API base URL | https://api.openai.com/v1 |
| SECRET_KEY | JWT signing key | change-in-production |
