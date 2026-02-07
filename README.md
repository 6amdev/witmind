# Witmind

AI Agent Platform - Tool for having AI agents help with work.

## Overview

Witmind เป็น platform สำหรับใช้ AI Agents ช่วยทำงานทุกประเภท
- เริ่มจาก Development work (coding, testing, deployment)
- ขยายไป Marketing, Creative และอื่นๆ

### Key Features

- **Multi-Agent System** - 21 agents ใน 3 ทีม (Dev, Marketing, Creative)
- **Mission Control** - Dashboard ติดตามงาน real-time
- **Unified CLI** - คำสั่ง `wit` สำหรับทุกการใช้งาน
- **LLM Router** - เลือก LLM ที่เหมาะกับงาน (Claude, OpenRouter, Ollama)

## Quick Start

```bash
# Clone repository
git clone git@github.com:6amdev/witmind.git ~/witmind
cd ~/witmind

# Run setup
./scripts/setup.sh

# Configure API keys
cp .env.example ~/.env
nano ~/.env  # Fill in your keys

# Start services
cd docker && docker compose up -d

# Create your first project
wit new "Build a Todo App with React"
wit run proj-xxx --auto-approve-all
```

## CLI Commands

### Project Management
```bash
wit new "Project description"        # Create new project
wit list                             # List all projects
wit run proj-xxx                     # Run workflow
wit run proj-xxx --auto-approve-all  # Auto approve all steps
wit logs proj-xxx --follow           # Watch logs
```

### Agent Commands
```bash
wit agent list                       # List all agents
wit agent run frontend_dev           # Run single agent
wit team list                        # List teams
```

### System Commands
```bash
wit status                           # System status
wit docker list                      # Docker containers
wit docker logs caddy                # View logs
```

### Cloud (DigitalOcean)
```bash
wit do account                       # Account info
wit do dns list 6amdev.com           # DNS records
wit do ddns 6amdev.com home          # Update DDNS
```

## Project Structure

```
witmind/
├── platform/               # Core platform
│   ├── core/               # Orchestrator, AgentRunner
│   ├── teams/              # Agent definitions
│   │   ├── dev/            # Development team (11 agents)
│   │   ├── marketing/      # Marketing team (5 agents)
│   │   └── creative/       # Creative team (5 agents)
│   └── workflows/          # Workflow definitions
│
├── cli/                    # wit CLI tool
│   ├── wit.py              # Main entry
│   └── commands/           # Command modules
│
├── mission-control/        # Dashboard
│   ├── backend/            # FastAPI + Socket.io
│   └── frontend/           # React + Vite
│
├── docker/                 # Docker configs
│   ├── docker-compose.yml
│   └── caddy/Caddyfile
│
├── scripts/                # Utility scripts
│   ├── setup.sh            # First-time setup
│   └── ddns-update.py      # DDNS updater
│
├── docs/                   # Documentation
├── .env.example            # Environment template
└── .gitignore              # Git ignore rules
```

## Agent Teams

### Development Team (11 agents)
| Agent | Role | LLM |
|-------|------|-----|
| pm | Project Manager | Claude Opus |
| business_analyst | Business Analyst | Claude Opus |
| tech_lead | Tech Lead/Architect | Claude Opus |
| uxui_designer | UX/UI Designer | Claude Sonnet |
| frontend_dev | Frontend Developer | Claude Sonnet |
| backend_dev | Backend Developer | Claude Sonnet |
| fullstack_dev | Fullstack Developer | Claude Sonnet |
| mobile_dev | Mobile Developer | Claude Sonnet |
| qa_tester | QA/Testing | Claude Sonnet |
| security_auditor | Security Auditor | Claude Opus |
| devops | DevOps Engineer | Claude Sonnet |

### Marketing Team (5 agents)
| Agent | Role |
|-------|------|
| marketing_lead | Strategy |
| content_writer | Blog/Articles |
| seo_specialist | SEO |
| social_media_manager | Social Media |
| copywriter | Ad Copy |

### Creative Team (5 agents)
| Agent | Role |
|-------|------|
| creative_director | Direction |
| graphic_designer | Graphics |
| ui_designer | UI/UX |
| video_editor | Video |
| motion_designer | Animation |

## LLM Presets

```bash
wit run proj-xxx --preset max_quality   # Opus for all (expensive)
wit run proj-xxx --preset balanced      # Mix Opus/Sonnet
wit run proj-xxx --preset cost_saving   # Sonnet/Haiku
wit run proj-xxx --preset local_only    # Ollama (free)
```

## Configuration

Copy `.env.example` to `~/.env` and fill in your values:

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-xxx      # For Claude agents
OPENROUTER_API_KEY=sk-or-xxx      # For OpenRouter models

# Optional
DO_API_TOKEN=dop_v1_xxx           # For DigitalOcean DDNS
OPENAI_API_KEY=sk-xxx             # For OpenAI models
```

## Storage Optimization (Optional)

For servers with SSD + HDD:

```
SSD (fast) - Active work
├── witmind/            # Code
├── witmind-data/       # Current projects
└── workspace/          # Development

HDD (large) - Archives
├── archives/           # Old projects
├── backups/            # Backups
└── media/              # Large files
```

See [docs/STORAGE.md](docs/STORAGE.md) for setup guide.

## Services (Production)

| URL | Service |
|-----|---------|
| https://mc.6amdev.com | Mission Control |
| https://api.6amdev.com | API |
| https://git.6amdev.com | Gitea |
| https://code.6amdev.com | VS Code |

## License

MIT License - 6amdev 2024-2026
