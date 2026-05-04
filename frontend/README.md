# AI Platform Frontend

## Quick Start

### Using Docker Compose

```bash
cd ai-platform
docker-compose up -d
```

### Local Development

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Set up environment variables:
```bash
cp .env.example .env.local
# Edit .env.local with your configuration
```

3. Run the development server:
```bash
npm run dev
```

4. Open [http://localhost:3000](http://localhost:3000)

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| NEXT_PUBLIC_API_URL | Backend API URL | http://localhost:8000 |

## Project Structure

```
frontend/
├── app/                 # Next.js App Router pages
│   ├── chat/           # Chat page
│   ├── agents/         # Agent management page
│   └── models/         # Model management page
├── components/         # React components
│   ├── chat/          # Chat-specific components
│   ├── ui/            # UI components (buttons, inputs, etc.)
│   └── ...
├── stores/            # Zustand state management
├── types/             # TypeScript type definitions
└── lib/               # Utility functions
```

## Features

- **Chat Interface**: Real-time streaming chat with AI models
- **Model Selection**: Switch between Ollama (local) and OpenAI (cloud) models
- **Agent Management**: Create and manage custom AI agents
- **Dark/Light Theme**: Toggle between light and dark modes
- **Responsive Design**: Works on desktop and mobile

## Tech Stack

- Next.js 14 (App Router)
- React 18
- TypeScript
- Tailwind CSS
- shadcn/ui
- Zustand (State Management)
