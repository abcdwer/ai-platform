# AI Platform - Quick Start Guide

Get up and running with AI Platform in minutes using Docker.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (v20.10+)
- [Docker Compose](https://docs.docker.com/compose/install/) (v2.0+)
- 4GB+ RAM (8GB+ recommended)
- 10GB+ free disk space

---

## Quick Start (5 minutes)

### 1. Clone & Configure

```bash
# Clone the repository
git clone https://github.com/your-repo/ai-platform.git
cd ai-platform

# Copy environment template
cp .env.example ./backend/.env

# Edit backend/.env to add your API keys (optional for local models)
```

### 2. Start Services

```bash
# Start all services in background
./start.sh

# Or use Docker Compose directly:
docker compose up -d
```

### 3. Access the Application

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| ChromaDB | http://localhost:8001 |

---

## Startup Options

### Basic Commands

```bash
# Start all services
./start.sh

# Start with Ollama (local AI models)
./start.sh --ollama

# Start with hot-reload enabled (development)
./start.sh --local

# Start and rebuild images
./start.sh --build
```

### Combining Options

```bash
# Local development with Ollama
./start.sh --local --ollama

# Production build with Ollama
./start.sh --build --ollama
```

### Docker Compose Direct Commands

```bash
# Standard startup
docker compose up -d

# With local development config
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d

# Rebuild and start
docker compose build && docker compose up -d
```

---

## Service Management

### View Logs

```bash
# All logs (follow mode)
./logs.sh -f

# Specific service
./logs.sh backend
./logs.sh -f frontend

# Last 500 lines
./logs.sh --tail 500

# With timestamps
./logs.sh --timestamps
```

### Stop Services

```bash
# Stop all services
./stop.sh

# Stop and remove data volumes
./stop.sh --volumes

# Stop and remove images
./stop.sh --images
```

### Check Status

```bash
docker compose ps
```

---

## Configuration

### Environment Variables

Edit `backend/.env` to configure:

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_PASSWORD` | postgres | PostgreSQL password |
| `SECRET_KEY` | (change me) | Session encryption key |
| `OPENAI_API_KEY` | - | OpenAI API key (optional) |
| `OLLAMA_BASE_URL` | host.docker.internal:11434 | Ollama endpoint |

### Generate Secret Key

```bash
openssl rand -hex 32
```

---

## Troubleshooting

### Services Won't Start

```bash
# Check Docker is running
docker ps

# Check ports are available
lsof -i :3000 -i :8000 -i :5432

# View error logs
./logs.sh --tail 100
```

### Database Connection Issues

```bash
# Wait for postgres to be ready
docker compose ps postgres

# Check postgres logs
./logs.sh postgres
```

### Frontend Can't Connect to Backend

1. Verify backend is running: `curl http://localhost:8000/docs`
2. Check `NEXT_PUBLIC_API_URL` in frontend config
3. Check CORS settings in `backend/.env`

### Ollama Not Working

```bash
# Pull a model
docker exec -it ai-platform-ollama ollama pull llama2

# Verify Ollama is running
curl http://localhost:11434/api/tags
```

### Reset Everything

```bash
# Stop all services and remove data
./stop.sh --volumes

# Remove images
./stop.sh --images

# Fresh start
./start.sh --build
```

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Frontend                          │
│               (Next.js - Port 3000)                  │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│                    Backend                           │
│              (FastAPI - Port 8000)                   │
└──────┬──────────┬──────────┬───────────┬────────────┘
       │          │          │           │
       ▼          ▼          ▼           ▼
┌──────────┐ ┌───────┐ ┌──────────┐ ┌──────────┐
│PostgreSQL│ │ Redis │ │ ChromaDB │ │  Ollama  │
│ :5432    │ │ :6379 │ │  :8001   │ │  :11434  │
└──────────┘ └───────┘ └──────────┘ └──────────┘
```

---

## Next Steps

- Read the full [README.md](./README.md)
- Explore the [API Documentation](http://localhost:8000/docs)
- Check out [DESIGN.md](./DESIGN.md) for architecture details
