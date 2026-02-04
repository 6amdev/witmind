# Project Structure Template

## เมื่อสร้างโปรเจคใหม่ ให้สร้างโครงสร้างดังนี้:

```
projects/active/{{PROJECT_ID}}/
├── .context/                    # Project context (ข้อมูลโปรเจค)
│   ├── project_context.yaml     # ข้อมูล client, constraints
│   ├── decisions_log.md         # บันทึกการตัดสินใจ
│   └── handoff_notes.md         # Notes ส่งต่อระหว่าง stages
│
├── .memory/                     # Agent memories (ความจำ per agent)
│   ├── pm.json
│   ├── tech_lead.json
│   ├── frontend_dev.json
│   ├── backend_dev.json
│   └── ...
│
├── docs/                        # Project documents
│   ├── SPEC.md                  # Requirements specification
│   ├── ARCHITECTURE.md          # System architecture
│   ├── TASKS.md                 # Task breakdown
│   ├── TECH_STACK.md            # Technology choices
│   ├── TEST_REPORT.md           # QA test results
│   ├── SECURITY_REPORT.md       # Security audit results
│   └── DEPLOY_INFO.md           # Deployment information
│
├── src/                         # Source code
│   └── [project-specific structure]
│
├── tests/                       # Test files
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── assets/                      # Static assets
│   ├── images/
│   ├── icons/
│   └── fonts/
│
├── PROJECT.yaml                 # Project configuration
├── README.md                    # Project readme
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore rules
└── CHANGELOG.md                 # Version history
```

## File Responsibilities

| File | Created By | Updated By |
|------|------------|------------|
| PROJECT.yaml | PM | All agents |
| SPEC.md | PM | PM, Tech Lead |
| ARCHITECTURE.md | Tech Lead | Tech Lead, Devs |
| TASKS.md | Tech Lead | All devs |
| TECH_STACK.md | Tech Lead | Tech Lead, DevOps |
| TEST_REPORT.md | QA | QA |
| SECURITY_REPORT.md | Security | Security |
| DEPLOY_INFO.md | DevOps | DevOps |
| .context/* | Orchestrator | All agents |
| .memory/* | Each agent | Each agent |

## Stage-by-Stage Creation

### Stage: Intake (PM)
Creates:
- PROJECT.yaml
- SPEC.md
- .context/project_context.yaml
- .memory/pm.json

### Stage: Design (Tech Lead)
Creates:
- ARCHITECTURE.md
- TASKS.md
- TECH_STACK.md
- .memory/tech_lead.json

### Stage: Development (Devs)
Creates:
- src/ (entire codebase)
- tests/
- .memory/[dev].json

### Stage: Testing (QA)
Creates:
- TEST_REPORT.md
- Additional tests
- .memory/qa_tester.json

### Stage: Security (Security)
Creates:
- SECURITY_REPORT.md
- .memory/security_auditor.json

### Stage: Deployment (DevOps)
Creates:
- DEPLOY_INFO.md
- Dockerfile
- docker-compose.yml
- .github/workflows/
- .memory/devops.json

### Stage: Delivery (PM)
Creates:
- DELIVERY.md
- Final handoff documents
