# Platform Templates

Templates สำหรับสร้าง agent และ configuration files

---

## 📁 Available Templates

| Template | Purpose | Use When |
|----------|---------|----------|
| `agent.template.yaml` | Agent definition | สร้าง agent ใหม่ |
| `prompt.template.md` | System prompt | สร้าง prompt สำหรับ agent |
| `MEMORY.template.md` | Agent memory | Agent ต้องจำข้อมูลข้าม sessions |

---

## 🚀 How to Use

### 1. Create New Agent

```bash
# Copy template
cp platform/templates/agent.template.yaml platform/teams/dev/agents/new_agent.yaml

# Edit with your agent details
code platform/teams/dev/agents/new_agent.yaml
```

### 2. Create Agent Prompt

```bash
# Copy template
cp platform/templates/prompt.template.md platform/prompts/new_agent.md

# Edit prompt content
code platform/prompts/new_agent.md
```

### 3. Create Agent Memory

```bash
# Create agent folder
mkdir -p platform/teams/dev/agents/new_agent/

# Copy template
cp platform/templates/MEMORY.template.md platform/teams/dev/agents/new_agent/MEMORY.md

# Edit memory file
code platform/teams/dev/agents/new_agent/MEMORY.md
```

---

## 📋 Checklist: New Agent

- [ ] Create agent YAML from `agent.template.yaml`
- [ ] Create prompt MD from `prompt.template.md`
- [ ] Create memory MD from `MEMORY.template.md` (optional)
- [ ] Add agent to team.yaml
- [ ] Update seed_agents.py (if applicable)
- [ ] Test agent execution

---

## 🔗 Related Files

- `CLAUDE.md` - Project context for Claude
- `.cursorrules` - Project context for Cursor
- `AI_CONTEXT.md` - Generic AI context
- `LEARNINGS.md` - Project lessons learned

---

*เมื่อสร้าง agent ใหม่ ให้ใช้ templates เหล่านี้เพื่อความสม่ำเสมอ*
