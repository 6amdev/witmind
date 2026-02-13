# Workflow Dashboard - Complete Guide

## 🎯 แนวคิดหลัก

### ปัญหาที่แก้:
**"บางงานไม่ต้องใช้ทุก agent - แต่ไม่รู้ว่าจะใช้ตัวไหนดี"**

### วิธีแก้:
**Workflow Templates** - ระบบเลือก agents ให้อัตโนมัติตามประเภทงาน

---

## 📋 Template System

### แนวคิด
```
งานแต่ละประเภท → ใช้ agents ที่ต่างกัน

Website ง่ายๆ:
  PM → Frontend Dev → QA
  (ไม่ต้องใช้ Backend, Security, DevOps)

Full-stack App:
  PM → Business Analyst → Tech Lead → UX/UI →
  Frontend + Backend (parallel) →
  QA → Security → DevOps
  (ใช้เกือบทุกตัว)

Mobile App:
  PM → Tech Lead → UX/UI → Mobile Dev → QA → DevOps
  (ไม่ใช้ Frontend/Backend)
```

### Templates ที่มี (9 แบบ)

#### 1. **Simple Website**
```yaml
Agents: PM → Frontend Dev → QA Tester
Use for: Landing page, portfolio, blog
Example: "สร้าง portfolio website"
```

#### 2. **Full-stack Application**
```yaml
Agents: PM → Business Analyst → Tech Lead → UX/UI Designer →
        Frontend Dev + Backend Dev (parallel) →
        QA → Security → DevOps
Use for: Complete web apps
Example: "สร้าง todo app ที่มี user authentication"
```

#### 3. **Mobile App**
```yaml
Agents: PM → Tech Lead → UX/UI → Mobile Dev → QA → DevOps
Use for: iOS/Android apps
Example: "สร้าง mobile app สำหรับจัดการงาน"
```

#### 4. **API Backend**
```yaml
Agents: PM → Tech Lead → Backend Dev → QA → Security → DevOps
Use for: REST API, microservices
Example: "สร้าง REST API สำหรับ blog"
```

#### 5. **Code Review**
```yaml
Agents: Tech Lead → Security Auditor → QA Tester
Use for: Review existing code
Example: "ตรวจ code ใน repo นี้"
```

#### 6. **Content Campaign**
```yaml
Agents: Marketing Lead → Content Writer + Copywriter (parallel) →
        SEO Specialist → Social Media Manager
Use for: Marketing content
Example: "สร้าง content campaign สำหรับ product launch"
```

#### 7. **SEO Optimization**
```yaml
Agents: SEO Specialist → Content Writer
Use for: Improve SEO
Example: "ปรับ SEO ให้ดีขึ้น"
```

#### 8. **Branding**
```yaml
Agents: Creative Director → Graphic Designer → UI Designer
Use for: Brand identity
Example: "สร้าง logo และ brand identity"
```

#### 9. **Video Production**
```yaml
Agents: Creative Director → Motion Designer → Video Editor
Use for: Video content
Example: "สร้าง promotional video"
```

---

## 🤖 Auto-Detection (Smart Mode)

ไม่ต้องเลือก template - ระบบเลือกให้อัตโนมัติ!

```javascript
// User describes what they want
"Build a mobile app for tracking expenses"

// System analyzes keywords
Keywords: ["mobile", "app"]
→ Suggests: MOBILE_APP template
→ Agents: PM, Tech Lead, UX/UI, Mobile Dev, QA, DevOps

// User describes
"Create a landing page for my product"

// System analyzes
Keywords: ["landing page", "website"]
→ Suggests: SIMPLE_WEBSITE template
→ Agents: PM, Frontend Dev, QA
```

### Algorithm (ตอนนี้ใช้ keyword matching)
```python
def suggest_template(description):
    if "mobile" or "ios" or "android" in description:
        return MOBILE_APP

    elif "website" or "landing" or "portfolio" in description:
        return SIMPLE_WEBSITE

    elif "api" or "backend" or "microservice" in description:
        return API_BACKEND

    # ... more rules

    else:
        return FULLSTACK_APP  # Default
```

**อนาคต:** ใช้ LLM วิเคราะห์ description แล้วเลือก template ที่เหมาะสม

---

## 🏗️ Architecture

### System Components

```
┌─────────────────────────────────────────────────────────┐
│                 Workflow Dashboard UI                    │
│              (Port 5000 - New!)                         │
│  - Template selection                                   │
│  - Real-time execution log                             │
│  - Agent status tracking                               │
└─────────────────────────────────────────────────────────┘
                         ↓ HTTP/WebSocket
┌─────────────────────────────────────────────────────────┐
│              Workflow Executor (NEW)                     │
│  - Load templates                                       │
│  - Auto-select agents                                   │
│  - Execute workflows                                    │
└─────────────────────────────────────────────────────────┘
                         ↓ Uses
┌─────────────────────────────────────────────────────────┐
│           Core Components (Phase 1-5)                    │
│  - IntelligentAgent (agentic loop)                      │
│  - WorkflowEngine (orchestration)                       │
│  - AgentTools (Read, Write, Bash, Git, etc.)            │
│  - Monitoring (metrics, costs)                          │
│  - Error Handling (retries, recovery)                   │
└─────────────────────────────────────────────────────────┘
                         ↓ Loads from
┌─────────────────────────────────────────────────────────┐
│            Agent Definitions (YAML)                      │
│  - platform/teams/dev/agents/*.yaml (11)                │
│  - platform/teams/marketing/agents/*.yaml (5)            │
│  - platform/teams/creative/agents/*.yaml (5)             │
│  Total: 21 Agents                                       │
└─────────────────────────────────────────────────────────┘
```

### New Files Created

```
platform/core/
├── agent_loader.py         # Load agents from YAML → IntelligentAgent
├── workflow_templates.py   # Template definitions (9 templates)
└── workflow_executor.py    # Execute workflows with templates

workflow-dashboard/
├── backend/
│   ├── main.py            # FastAPI server (port 5000)
│   └── requirements.txt
├── frontend/
│   └── index.html         # Dashboard UI
├── README.md
└── start.sh               # Startup script
```

---

## 🆚 Comparison: Mission Control vs Workflow Dashboard

### Mission Control (Port 4001)
```
📦 Project Management System

Concept:
  - Jira/Trello-like interface
  - Kanban board
  - Manual task creation
  - Human assigns tasks to agents

Workflow:
  1. Human creates project
  2. Human creates tasks
  3. Human assigns task to agent
  4. Agent executes task
  5. Human checks result
  6. Repeat

Pros:
  ✅ Full control
  ✅ Clear task tracking
  ✅ Good for team management

Cons:
  ❌ Manual effort required
  ❌ Human needs to know which agents to use
  ❌ No automation
```

### Workflow Dashboard (Port 5000 - NEW)
```
🤖 Autonomous Workflow System

Concept:
  - GitHub Actions/Zapier-like
  - Template-based
  - Auto agent selection
  - End-to-end automation

Workflow:
  1. Human describes what they want
  2. System picks template
  3. System selects agents
  4. Agents execute automatically (PM → TL → Dev → QA → DevOps)
  5. Deliverables appear in project folder

Pros:
  ✅ Fully autonomous
  ✅ Smart template selection
  ✅ Just describe, it builds
  ✅ See agent thinking in real-time

Cons:
  ❌ Less control (more black box)
  ❌ Templates might not fit all cases
```

### Which to Use?

```
Use Mission Control when:
  - You want full control over each step
  - You're managing a team of agents
  - You need to micromanage tasks
  - You want Kanban-style tracking

Use Workflow Dashboard when:
  - You want automation
  - You just want to describe and get results
  - You trust agents to work autonomously
  - You want end-to-end workflows
```

### Can They Work Together?

**YES!** They can complement each other:

```
Workflow Dashboard:
  - Start automated workflows
  - Get quick prototypes
  - Handle standard patterns

Mission Control:
  - Fine-tune individual tasks
  - Handle edge cases
  - Team collaboration
  - Manual adjustments
```

---

## 🚀 Usage Examples

### Example 1: Quick Website
```bash
# Via UI (http://localhost:5000)
Project Name: my_portfolio
Description: Create a personal portfolio website with dark theme
Template: Auto-detect
→ System picks: Simple Website
→ Agents: PM, Frontend Dev, QA
→ Result: Complete website in workflow_projects/my_portfolio/
```

### Example 2: Full App
```bash
# Via API
curl -X POST http://localhost:5000/api/projects/execute \
  -H "Content-Type: application/json" \
  -d '{
    "name": "expense_tracker",
    "description": "Build an expense tracking app with user auth",
    "template_id": "fullstack_app",
    "auto_approve": true
  }'

→ Agents: PM → BA → Tech Lead → UX/UI →
          Frontend + Backend (parallel) →
          QA → Security → DevOps
→ Result: Complete app with frontend, backend, tests, deployment
```

### Example 3: Mobile App
```bash
# Via UI
Description: "Build a mobile app for iOS to track daily habits"
Template: Auto-detect
→ System picks: Mobile App
→ Agents: PM, Tech Lead, UX/UI, Mobile Dev, QA, DevOps
```

---

## 📊 Future Enhancements

### 1. Custom Templates (User-Defined)
```yaml
# custom_templates/my_template.yaml
name: "E-commerce Site"
description: "Full e-commerce with payment"
agents:
  - pm
  - business_analyst
  - tech_lead
  - uxui_designer
  - frontend_dev
  - backend_dev
  - qa_tester
  - security_auditor  # Important for payment!
  - devops
```

### 2. LLM-Powered Template Selection
```python
# Instead of keyword matching, use LLM to analyze
prompt = f"""
Given this project description:
{description}

Which template is most appropriate?
- simple_website
- fullstack_app
- mobile_app
- ...

Consider:
- Complexity
- Required features
- Timeline
- Team size needed
"""

template = llm.chat(prompt)
```

### 3. Dynamic Agent Selection
```python
# Don't just use fixed templates
# Let PM analyze and decide which agents are needed

pm_analysis = pm.analyze(description)
→ "This needs: Frontend, Backend, Security (payment), QA, DevOps"

agents_needed = ['frontend_dev', 'backend_dev', 'security_auditor', 'qa_tester', 'devops']
```

### 4. Conditional Agents
```yaml
template: fullstack_app
agents:
  - pm
  - tech_lead
  - frontend_dev
  - backend_dev
  - qa_tester
  - security_auditor:
      condition: "has_payment OR has_auth OR handles_sensitive_data"
  - devops:
      condition: "deployment_required"
```

---

## 🎓 Best Practices

### When to Create New Templates

Create a new template when:
1. You repeatedly build the same type of thing
2. There's a clear pattern of agents needed
3. Existing templates don't fit

Example:
```
Pattern: "Data Analysis Projects"
Always need: PM, Data Analyst, Data Scientist, QA

Create template:
  id: data_analysis
  agents: [pm, data_analyst, data_scientist, qa_tester]
```

### Template Naming

Good names are:
- **Specific**: "mobile_app" not "app"
- **Action-oriented**: "code_review" not "review"
- **Clear scope**: "simple_website" vs "fullstack_app"

### Agent Selection Tips

```
Too few agents:
  ❌ "Just use Frontend Dev for everything"
  → No architecture design
  → No testing
  → No deployment

Too many agents:
  ❌ "Use all 21 agents for a landing page"
  → Overkill
  → Slow
  → Expensive

Just right:
  ✅ Match agents to actual needs
  ✅ Use templates as starting point
  ✅ Customize when needed
```

---

## 📈 Metrics & Monitoring

Future dashboard will show:

```
Template Usage:
  fullstack_app:    45%
  simple_website:   30%
  mobile_app:       15%
  content_campaign: 10%

Success Rates:
  fullstack_app:    85% (34/40 successful)
  simple_website:   95% (28/29 successful)

Average Costs:
  fullstack_app:    $2.50 per execution
  simple_website:   $0.30 per execution

Average Duration:
  fullstack_app:    25 minutes
  simple_website:   5 minutes
```

---

## 🎉 Summary

### What We Built:

1. **agent_loader.py** - โหลด 21 agents จาก YAML
2. **workflow_templates.py** - 9 templates สำหรับงานแต่ละแบบ
3. **workflow_executor.py** - Execute workflows ด้วย templates
4. **Dashboard UI** - Port 5000, visual interface
5. **Auto-detection** - ระบบเลือก template ให้อัตโนมัติ

### Key Innovation:

**"Smart Agent Selection"** - ไม่ต้องรู้ว่าต้องใช้ agent ไหน ระบบเลือกให้!

### Result:

```
Before:
  "ผมต้องใช้ PM, Tech Lead, Frontend Dev, QA, DevOps ใช่มั้ย?"
  → สับสน

After:
  "Build a portfolio website"
  → System: "Use Simple Website template (PM, Frontend, QA)"
  → Auto-executes
  → Done!
```

---

ง่ายและฉลาดขึ้นมาก! 🚀
