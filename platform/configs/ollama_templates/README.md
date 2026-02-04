# Ollama Agent Templates

## Available Models on Server (192.168.80.203)

| Model | Parameters | Size | Best For |
|-------|------------|------|----------|
| `llama3:latest` | 8B | 4.66 GB | General tasks, documentation |
| `deepseek-r1:8b` | 8.2B | 5.23 GB | Reasoning, analysis, complex thinking |
| `qwen2.5-coder:7b` | 7.6B | 4.68 GB | Code generation, programming |

## Agent → Model Mapping

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        OLLAMA AGENT CONFIGURATION                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐            │
│  │   ANALYSIS   │     │  MANAGEMENT  │     │ DEVELOPMENT  │            │
│  │    ROLES     │     │    ROLES     │     │    ROLES     │            │
│  └──────┬───────┘     └──────┬───────┘     └──────┬───────┘            │
│         │                    │                    │                     │
│         ▼                    ▼                    ▼                     │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐            │
│  │ deepseek-r1  │     │    llama3    │     │qwen2.5-coder │            │
│  │     :8b      │     │   :latest    │     │     :7b      │            │
│  └──────────────┘     └──────────────┘     └──────────────┘            │
│         │                    │                    │                     │
│         ▼                    ▼                    ▼                     │
│  • business_analyst   • pm                 • backend_dev               │
│  • security_auditor   • uxui_designer      • frontend_dev              │
│  • tech_lead          • qa_tester          • fullstack_dev             │
│                                            • devops                     │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Configuration Templates

### Template A: Coding Focus (qwen2.5-coder dominant)
Best for: API development, code-heavy projects

### Template B: Reasoning Focus (deepseek-r1 dominant)
Best for: Complex business logic, architecture decisions

### Template C: Balanced (mixed models)
Best for: Full project lifecycle

### Template D: Speed Focus (llama3 for all)
Best for: Quick prototypes, simple projects

## Usage

```bash
# Use Template A
wit run my-project --preset ollama_coding

# Use Template B
wit run my-project --preset ollama_reasoning

# Use Template C (default local_only)
wit run my-project --preset local_only

# Use Template D
wit run my-project --preset ollama_speed
```
