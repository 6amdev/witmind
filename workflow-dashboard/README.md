# Witmind Workflow Dashboard

🤖 **Autonomous AI Agent Workflows** - Visual dashboard for executing multi-agent workflows.

## Features

### 🎯 Smart Workflow Templates
- **Auto-detection** - Just describe what you want, AI picks the right template
- **9 Pre-built Templates**:
  - Simple Website (PM → Frontend → QA)
  - Full-stack App (PM → BA → Tech Lead → UX → Frontend/Backend → QA → Security → DevOps)
  - Mobile App (PM → Tech Lead → UX → Mobile → QA → DevOps)
  - API Backend (PM → Tech Lead → Backend → QA → Security → DevOps)
  - Code Review (Tech Lead → Security → QA)
  - Content Campaign (Marketing Lead → Content Writer → SEO → Social Media)
  - SEO Optimization (SEO → Content Writer)
  - Branding (Creative Director → Graphic Designer → UI Designer)
  - Video Production (Creative Director → Motion Designer → Video Editor)

### 🤖 All 21 AI Agents
- **Dev Team (11)**: PM, Business Analyst, Tech Lead, UX/UI Designer, Frontend Dev, Backend Dev, Fullstack Dev, Mobile Dev, QA Tester, Security Auditor, DevOps
- **Marketing Team (5)**: Marketing Lead, Content Writer, SEO Specialist, Social Media Manager, Copywriter
- **Creative Team (5)**: Creative Director, Graphic Designer, UI Designer, Video Editor, Motion Designer

### ✨ Real-time Features
- Live execution log
- Agent status tracking
- WebSocket updates
- Cost tracking (future)
- Parallel execution visualization (future)

---

## Differences from Mission Control

| Feature | Mission Control (Port 4001) | Workflow Dashboard (Port 5000) |
|---------|----------------------------|--------------------------------|
| **Concept** | Project Management (Jira-like) | Workflow Automation |
| **Control** | Manual task assignment | Autonomous execution |
| **UI** | Kanban board | Flow diagram + Thinking log |
| **Execution** | Task-by-task | End-to-end workflow |
| **Intelligence** | Simple agents | IntelligentAgent (agentic loop) |
| **Templates** | No templates | Smart template selection |
| **Use Case** | Manage tasks | "Just describe, it builds" |

---

## Quick Start

### 1. Install Dependencies

```bash
cd ~/witmind/workflow-dashboard/backend
pip install -r requirements.txt
```

### 2. Set Environment Variables

Make sure you have `~/.env` with:
```bash
OPENROUTER_API_KEY=sk-or-v1-...
# Or
ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Start Dashboard

```bash
cd ~/witmind/workflow-dashboard/backend
python3 main.py
```

### 4. Access Dashboard

- **Dashboard**: http://localhost:5000
- **API Docs**: http://localhost:5000/docs

---

## How It Works

### 1. User describes what they want
```
"Build a portfolio website with dark theme"
```

### 2. System picks best template
```
Template: Simple Website
Agents: PM → Frontend Dev → QA Tester
```

### 3. Workflow executes autonomously
```
PM:
  - Reads description
  - Creates SPEC.md
  - Defines requirements

Frontend Dev:
  - Reads SPEC.md
  - Creates HTML/CSS/JS
  - Implements dark theme

QA Tester:
  - Tests the website
  - Creates TEST_REPORT.md
```

### 4. Deliverables appear in project folder
```
workflow_projects/my_portfolio/
├── REQUEST.md
├── SPEC.md
├── src/
│   ├── index.html
│   ├── style.css
│   └── script.js
└── TEST_REPORT.md
```

---

## Architecture

```
workflow-dashboard/
├── backend/
│   ├── main.py              # FastAPI server
│   └── requirements.txt
└── frontend/
    └── index.html           # Dashboard UI

platform/core/               # Shared with all systems
├── agent_loader.py          # Load agents from YAML
├── workflow_templates.py    # Template definitions
├── workflow_executor.py     # Execute workflows
├── intelligent_agent.py     # Agentic loop
├── workflow_engine.py       # Orchestration
└── agent_tools.py           # Real tools

platform/teams/              # Agent definitions
├── dev/agents/*.yaml        # 11 dev agents
├── marketing/agents/*.yaml  # 5 marketing agents
└── creative/agents/*.yaml   # 5 creative agents
```

---

## API Endpoints

### Get Templates
```bash
GET /api/templates
```

### Suggest Template
```bash
GET /api/templates/suggest?description=Build+a+mobile+app
```

### Execute Workflow
```bash
POST /api/projects/execute
{
  "name": "my_project",
  "description": "What you want to build",
  "template_id": "fullstack_app",  # or null for auto-detect
  "auto_approve": true
}
```

### List Projects
```bash
GET /api/projects
```

---

## Examples

### Example 1: Simple Website
```bash
curl -X POST http://localhost:5000/api/projects/execute \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my_portfolio",
    "description": "Create a personal portfolio website with dark theme",
    "auto_approve": true
  }'
```

### Example 2: Full-stack App
```bash
curl -X POST http://localhost:5000/api/projects/execute \
  -H "Content-Type: application/json" \
  -d '{
    "name": "todo_app",
    "description": "Build a todo app with React frontend and Node.js backend",
    "template_id": "fullstack_app",
    "auto_approve": true
  }'
```

---

## Future Enhancements

1. **Real-time Agent Thinking** - Show what each agent is thinking
2. **Cost Dashboard** - Track LLM costs per workflow
3. **Approval Gates** - Manual approval between stages
4. **Custom Templates** - Create your own templates
5. **Agent Chat** - Talk to agents during execution
6. **Parallel Visualization** - See parallel agents working
7. **Metrics Dashboard** - Success rates, costs, timing

---

## License

MIT
