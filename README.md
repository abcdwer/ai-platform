# AI Platform

A unified interface for local and cloud AI models. Chat with AI, create agents, fine-tune models, and integrate external tools in one powerful platform.

## Features

### Core Features
- **Multi-Model Support**: Connect to Ollama (local), OpenAI, Anthropic, and more
- **Agent System**: Create custom AI agents with specific prompts and tools
- **Conversation Management**: Organize, search, and manage your conversations
- **Real-time Streaming**: Get instant AI responses with streaming
- **Tool Integration**: Agents can search the web, execute code, and more
- **Dark/Light Mode**: Modern UI with theme support

### Phase 5: LoRA Fine-tuning
- **Dataset Management**: Upload and validate training datasets (JSONL, CSV, Parquet)
- **Multi-format Support**: Conversation, ShareGPT, and Alpaca formats
- **Training Modes**: LoRA, QLoRA, and Full fine-tuning
- **Real-time Monitoring**: Live loss curves, GPU utilization, training logs
- **Model Management**: Export, deploy, and manage fine-tuned models

### Phase 6: MCP (Model Context Protocol)
- **Server Management**: Configure and manage MCP servers
- **Transport Support**: SSE, Stdio, and HTTP Stream connections
- **Tool Discovery**: Auto-discover tools from connected servers
- **Tool Testing**: Test MCP tools directly from the UI
- **Call Logging**: Track all MCP tool invocations

### Additional Features
- **Knowledge Base**: Upload documents and chat with your data
- **Workflow Engine**: Build automated AI workflows
- **Multi-Agent Orchestration**: Coordinate multiple AI agents

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, PostgreSQL
- **Frontend**: Next.js 14, React, Tailwind CSS, Zustand
- **Database**: PostgreSQL with async support
- **AI Models**: Ollama, OpenAI API

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- (Optional) Ollama for local models

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your settings

# Run database migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy and configure environment
cp .env.example .env.local
# Edit .env.local with your API URL

# Start development server
npm run dev
```

## Docker Deployment

### Prerequisites

- Docker Engine 20.10+
- Docker Compose v2.0+ (or Docker Compose plugin)

### Quick Start

```bash
# 1. Clone and navigate to project
cd ai-platform

# 2. Configure environment
cp .env.example backend/.env
# Edit backend/.env with your settings (especially SECRET_KEY)

# 3. Start all services
./start.sh

# Or use docker-compose directly
docker-compose up -d
```

### Start Options

```bash
# Standard start (connects to Ollama on host machine)
./start.sh

# Include Ollama service in Docker
./start.sh --ollama

# Rebuild images before starting
./start.sh --build

# Local development mode
./start.sh --local
```

### Service Management

```bash
# View all services status
docker-compose ps

# View logs (all services)
./logs.sh

# View logs (specific service)
./logs.sh backend
./logs.sh -f frontend

# Stop all services
./stop.sh

# Stop and remove data volumes (WARNING: data loss!)
./stop.sh --volumes
```

### Access URLs

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Documentation | http://localhost:8000/docs |
| ChromaDB | http://localhost:8001 |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |
| Ollama (optional) | http://localhost:11434 |

## Environment Configuration

### Backend Configuration (.env)

Copy `.env.example` to `backend/.env` and configure:

```env
# Required: Change this in production!
SECRET_KEY=your-secret-key-here

# Database (defaults work for Docker)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=aiplatform

# Ollama (for local models)
# - macOS/Windows with Docker Desktop: http://host.docker.internal:11434
# - Linux: http://172.17.0.1:11434
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_DEFAULT_MODEL=llama2

# Optional: Cloud AI providers
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
```

### Frontend Configuration (.env.local)

The frontend reads from environment at build time. For Docker deployment, configure `NEXT_PUBLIC_API_URL` in `docker-compose.yml` or as environment variable.

## First-Time Setup

1. **Configure environment**
   ```bash
   cp .env.example backend/.env
   nano backend/.env  # Edit SECRET_KEY and other settings
   ```

2. **Start services**
   ```bash
   ./start.sh
   ```

3. **Verify services are running**
   ```bash
   docker-compose ps
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - API Docs: http://localhost:8000/docs

5. **For local models with Ollama**
   - Install Ollama: https://ollama.ai/
   - Pull a model: `ollama pull llama2`
   - Start Ollama: `ollama serve`
   - Or run Ollama in Docker: `./start.sh --ollama`

## Troubleshooting

### Services won't start

```bash
# Check Docker is running
docker info

# Check port conflicts
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
lsof -i :8000  # Backend
lsof -i :8001  # ChromaDB
lsof -i :3000  # Frontend

# Check logs for errors
docker-compose logs backend
```

### Database connection errors

```bash
# Ensure PostgreSQL is healthy
docker-compose ps postgres

# Check database logs
docker-compose logs postgres

# Recreate database if corrupted
./stop.sh --volumes
./start.sh
```

### Frontend can't connect to backend

```bash
# Check backend is running
curl http://localhost:8000/docs

# Verify CORS settings in backend/.env
CORS_ORIGINS=["http://localhost:3000"]

# Check NEXT_PUBLIC_API_URL
docker-compose exec frontend env | grep NEXT_PUBLIC
```

### Out of disk space

```bash
# Clean up unused Docker resources
docker system prune -a
docker volume prune

# Remove old images
docker image prune -a
```

### Ollama not connecting (Linux)

If Ollama is running on the host but not accessible from containers:

```bash
# Option 1: Set host IP in .env
OLLAMA_BASE_URL=http://172.17.0.1:11434

# Option 2: Allow Ollama to listen on all interfaces
# Add to /etc/ollama/ollama.conf:
OLLAMA_HOST=0.0.0.0

# Option 3: Run Ollama with host network
# In docker-compose.yml, add to ollama service:
# network_mode: host
```

## Production Deployment

For production deployments:

1. **Use strong secrets**
   ```bash
   # Generate a secure secret key
   openssl rand -hex 32
   ```

2. **Configure SSL/TLS**
   - Use Nginx with Let's Encrypt
   - Or deploy behind a cloud load balancer

3. **Set appropriate environment variables**
   ```bash
   DEBUG=false
   NODE_ENV=production
   ```

4. **Use external databases**
   - Consider managed PostgreSQL (AWS RDS, Cloud SQL)
   - Consider managed Redis (Redis Cloud, ElastiCache)

5. **Secure CORS origins**
   ```env
   CORS_ORIGINS=["https://your-domain.com"]
   ```

## Quick Start

## Environment Variables

### Backend (.env)

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/aiplatform

# Ollama (local models)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_DEFAULT_MODEL=llama2

# OpenAI (optional)
OPENAI_API_KEY=your-api-key

# Security
SECRET_KEY=your-secret-key

# CORS
CORS_ORIGINS=["http://localhost:3000"]
```

### Frontend (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
ai-platform/
├── backend/
│   ├── app/
│   │   ├── agents/          # Agent system
│   │   ├── api/routes/      # API endpoints
│   │   ├── core/            # Config, database
│   │   ├── models/          # Database models & schemas
│   │   └── services/        # Business logic
│   ├── alembic/             # Database migrations
│   └── requirements.txt
├── frontend/
│   ├── app/                 # Next.js pages
│   ├── components/         # React components
│   ├── stores/              # Zustand stores
│   └── types/               # TypeScript types
└── docker-compose.yml
```

## API Endpoints

### Chat
- `POST /api/chat` - Send a chat message
- `POST /api/chat/stream` - Stream chat response

### Conversations
- `GET /api/conversations` - List conversations
- `POST /api/conversations` - Create conversation
- `GET /api/conversations/:id` - Get conversation
- `PUT /api/conversations/:id` - Update conversation
- `DELETE /api/conversations/:id` - Delete conversation
- `POST /api/conversations/:id/pin` - Pin/unpin conversation

### Agents
- `GET /api/agents` - List agents
- `POST /api/agents` - Create agent
- `GET /api/agents/:id` - Get agent
- `PUT /api/agents/:id` - Update agent
- `DELETE /api/agents/:id` - Delete agent

### Models
- `GET /api/models` - List available models
- `GET /api/models/status` - Get provider status
- `GET /api/models/health` - Health check

### Tools
- `GET /api/tools` - List available tools

## Development

### Running Tests
```bash
cd backend
pytest

cd ../frontend
npm run test
```

### Building for Production

```bash
# Backend
cd backend
pip install -r requirements.txt
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker

# Frontend
cd frontend
npm run build
npm start
```

## License

MIT License

## User & Auth Module (New)

### Backend Features
- User model with complete profile fields (email, username, password hash, avatar, bio)
- JWT token authentication with bcrypt password hashing
- OAuth2PasswordBearer scheme for API authentication
- User registration with email/username validation
- Login with JSON or form-based authentication
- Profile update and password change endpoints
- User data isolation (all user data scoped by user_id)

### Frontend Features
- Login page (`/auth/login`)
- Registration page (`/auth/register`)
- User profile section in sidebar with avatar
- Updated settings page with profile management
- Persistent auth state using Zustand with localStorage

### API Endpoints
- `POST /api/auth/register` - Create new user account
- `POST /api/auth/login` - Login (form-based)
- `POST /api/auth/login/json` - Login (JSON body)
- `GET /api/auth/me` - Get current user info
- `PUT /api/auth/me` - Update profile
- `POST /api/auth/refresh` - Refresh token
- `POST /api/auth/logout` - Logout
- `GET /api/auth/onboarding` - Get onboarding data
- `POST /api/auth/init-samples` - Initialize sample data

## Sample Data Module (New)

### Pre-built Knowledge Bases
1. **AI & Machine Learning Basics** - Introduction to ML concepts
2. **Product Design Guide** - User research and prototyping
3. **Programming & Development** - Python and API design guides
4. **Project Management** - Agile and task management

### Pre-built Workflow Templates
1. **Content Creation Workflow** - Topic → Research → Draft → Review → Finalize
2. **Code Review Workflow** - Syntax, Security, Best Practices analysis
3. **Data Analysis Workflow** - Ingestion → Analysis → Insights → Report

### Pre-built Example Conversations
1. **Getting Started with AI Agents** - Introduction to agent system
2. **Building a Knowledge Base** - How to use RAG features
3. **Automating Workflows** - Workflow automation tutorial

### Onboarding Experience
- Welcome message for new users
- Interactive checklist with quick actions
- Automatic sample data creation on registration

## Database Migrations

Run migrations to create the complete schema:
```bash
cd backend
alembic upgrade head
```

### Migration 002: Adds Complete Schema
- Users: additional fields (avatar_url, bio, preferences, last_login)
- Knowledge bases: user_id for data isolation
- Documents, Workflows, Multi-Agent, Fine-tuning, MCP tables

## Authentication Middleware

All API routes now require JWT authentication:
- Token in Authorization header: `Bearer <token>`
- Automatic user_id injection for data isolation
- Updated routes: conversations, chat, agents, knowledge, workflows, multi-agent

### Protected Routes Example
```python
@router.get("/protected")
async def protected_endpoint(
    current_user: User = Depends(get_current_user)
):
    return {"user_id": current_user.id}
```
