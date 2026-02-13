# Mission Control v2

AI Agent Task Management System - Real-time dashboard for managing AI development teams.

## Features

- 📁 **Projects** - Create and manage projects with auto team detection
- 📋 **Kanban Board** - Drag-and-drop task management
- 🤖 **21 AI Agents** - Dev, Marketing, and Creative teams
- ⚡ **Real-time Updates** - WebSocket-based live updates
- 🎨 **Dark Theme** - Beautiful, modern UI

## Tech Stack

**Backend:**
- Python FastAPI
- MongoDB (Motor async driver)
- Socket.io
- Redis (pub/sub)

**Frontend:**
- React 18 + TypeScript
- Vite
- Tailwind CSS
- @dnd-kit (drag & drop)
- Zustand (state management)
- React Query (server state)

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Infrastructure running (MongoDB, Redis) from root `docker-compose.yml`

### Development

```bash
# Start infrastructure (if not already running)
cd ../..
docker compose up -d

# Start Mission Control v2
cd projects/mission-control-v2
docker compose up -d --build
```

### Access

- **Frontend:** http://localhost:4001
- **Backend API:** http://localhost:4000
- **API Docs:** http://localhost:4000/docs

## Project Structure

```
mission-control-v2/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI app + Socket.io
│   │   ├── config.py         # Settings
│   │   ├── database.py       # MongoDB connection
│   │   ├── models/           # Pydantic models
│   │   ├── routes/           # API endpoints
│   │   └── services/         # Business logic
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── pages/            # Route pages
│   │   ├── hooks/            # Custom hooks
│   │   ├── stores/           # Zustand stores
│   │   ├── services/         # API calls
│   │   └── types/            # TypeScript types
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## API Endpoints

### Projects
- `GET /api/projects` - List all projects
- `POST /api/projects` - Create project (auto team detection)
- `GET /api/projects/:id` - Get project
- `PATCH /api/projects/:id` - Update project
- `DELETE /api/projects/:id` - Delete project
- `POST /api/projects/:id/start` - Start project

### Tasks
- `GET /api/projects/:id/tasks` - List tasks
- `POST /api/projects/:id/tasks` - Create task
- `PATCH /api/tasks/:id` - Update task
- `PATCH /api/tasks/:id/move` - Move task (Kanban)
- `DELETE /api/tasks/:id` - Delete task

### Agents
- `GET /api/agents` - List all agents
- `GET /api/agents?team=dev` - Filter by team
- `GET /api/agents/:id` - Get agent

## WebSocket Events

### Server → Client
- `task:update` - Task updated
- `activity:new` - New activity
- `agent:status` - Agent status change
- `agent:output` - Agent output (streaming)

### Client → Server
- `join_project` - Join project room
- `leave_project` - Leave project room

## Development

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:socket_app --reload --port 4000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## License

MIT
