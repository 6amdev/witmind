# Multi-Agent System Architecture

## ปัญหาที่พบ (และวิธีแก้)

### 1. Agent ไม่รู้ว่าจะ "ฉลาด" ยังไง? ❌

**ปัญหา:** ตอนนี้ agent มีแค่ config (YAML) แต่ไม่มี "สมอง" ที่ทำให้มันทำงานได้จริง

**วิธีแก้:**
```
Agent = System Prompt + Tools + Memory + Context
```

แต่ละ agent ต้องมี:
- **System Prompt ที่ชัดเจน**: บอกว่ามันเป็นใคร ทำอะไรได้บ้าง ขอบเขตอะไร
- **Tools**: ให้เครื่องมือที่เหมาะสม (Read, Write, Bash สำหรับ dev agent)
- **Memory**: จำว่าเคยทำอะไรไปแล้วบ้าง
- **Context**: รู้ว่าตอนนี้อยู่ในขั้นตอนไหน project อะไร

### 2. Agents ทำงานร่วมกันยังไง? ❌

**ปัญหา:** ไม่มีการส่งต่องาน - แต่ละ agent ทำแยกกัน

**วิธีแก้: Workflow Engine**

```
[PM Agent]
   ↓ สร้าง SPEC.md + TASKS.md
[Tech Lead]
   ↓ สร้าง ARCHITECTURE.md + TECH_STACK.md
[Frontend Dev]
   ↓ อ่าน ARCHITECTURE + TASKS → เขียน code
[QA Tester]
   ↓ อ่าน code → ทดสอบ → สร้าง TEST_REPORT.md
[DevOps]
   ↓ อ่าน ARCHITECTURE → Deploy
```

**Key Insight**: Agents สื่อสารผ่าน**ไฟล์** ไม่ใช่คุยกัน

### 3. ควบคุมการทำงานยังไง? ❌

**ปัญหา:** ไม่รู้ว่า agent ทำอะไรอยู่ หรือทำถูก/ผิด

**วิธีแก้: State Management + Approval Gates**

```python
# State Management
project_state = {
    'current_stage': 'frontend_dev',
    'completed_stages': ['pm', 'tech_lead', 'uxui_designer'],
    'pending_approvals': [],
    'deliverables': {
        'SPEC.md': '✅',
        'ARCHITECTURE.md': '✅',
        'src/': '⏳'
    }
}

# Approval Gate
if agent_output.needs_review():
    approval_gate.request_approval(user, agent_output)
    wait_for_approval()
else:
    proceed_to_next_agent()
```

### 4. ทำงานต่อเนื่องยังไง? ❌

**ปัญหา:** Agent ตอบครั้งเดียวแล้วจบ ไม่ได้ทำงานต่อเนื่อง

**วิธีแก้: Agentic Loop**

```python
def run_agent_with_loop(agent, task, max_iterations=10):
    for i in range(max_iterations):
        # 1. Agent คิดว่าต้องทำอะไร
        thought = agent.think(task, context)

        # 2. Agent ตัดสินใจ action
        action = agent.decide_action(thought)

        # 3. Execute action
        result = execute(action)

        # 4. Agent ประเมินผล
        evaluation = agent.evaluate(result, task)

        # 5. ถ้างานเสร็จ → จบ
        if evaluation.is_complete:
            return result

        # 6. ถ้ายังไม่เสร็จ → วนทำต่อ
        task = evaluation.next_task
```

---

## สถาปัตยกรรมที่ถูกต้อง

### Layer 1: Agent Core (สมองของ Agent)

```python
class IntelligentAgent:
    """Agent ที่มีสมองจริงๆ"""

    def __init__(self, config, llm_client, tools):
        self.config = config  # จาก YAML
        self.llm = llm_client  # Claude Code / Opus / Sonnet
        self.tools = tools  # Read, Write, Bash, etc.
        self.memory = AgentMemory()  # จำว่าเคยทำอะไร

    def execute_task(self, task):
        """วง Agentic Loop"""
        context = self.build_context(task)

        for iteration in range(self.max_iterations):
            # คิด
            response = self.llm.chat(
                system=self.config['system_prompt'],
                messages=context,
                tools=self.tools
            )

            # ทำ
            if response.wants_to_use_tool:
                tool_result = self.execute_tool(response.tool_call)
                context.append(tool_result)
                continue

            # เช็คว่างานเสร็จหรือยัง
            if response.declares_complete:
                return response.output

        return {"error": "Max iterations reached"}
```

### Layer 2: Workflow Engine (ควบคุมการทำงานร่วมกัน)

```python
class WorkflowEngine:
    """ควบคุม workflow ของทั้ง team"""

    def execute_workflow(self, project, workflow_def):
        """
        workflow_def = [
            {'agent': 'pm', 'task': 'analyze_requirements'},
            {'agent': 'tech_lead', 'task': 'design_architecture'},
            {'agent': 'frontend_dev', 'task': 'implement_ui',
             'condition': 'has_architecture'},
        ]
        """

        for stage in workflow_def:
            # ตรวจเช็ค condition
            if not self.check_condition(stage.get('condition')):
                continue

            # สร้าง agent
            agent = self.create_agent(stage['agent'])

            # สร้าง task context
            task = self.prepare_task(project, stage)

            # Run agent
            result = agent.execute_task(task)

            # บันทึกผล
            self.save_deliverables(project, result)

            # Approval gate (ถ้าต้องการ)
            if stage.get('needs_approval'):
                if not self.request_approval(result):
                    break

            # แจ้ง agent ตัวต่อไป
            self.notify_next_agent(stage.get('next_agent'))
```

### Layer 3: Communication Protocol (Agents สื่อสารกัน)

```
Project Structure:
project-xxx/
├── PROJECT.yaml          # Metadata
├── SPEC.md               # จาก PM
├── ARCHITECTURE.md       # จาก Tech Lead
├── TASKS.md              # รายการงาน
├── src/                  # Code จาก developers
├── tests/                # Tests จาก QA
├── .witmind/             # Internal state
│   ├── state.json        # Current state
│   ├── history.jsonl     # Agent actions log
│   └── approvals/        # Pending approvals
└── DELIVERABLES.md       # สรุปผลงาน
```

**Communication Flow:**
1. PM เขียน `SPEC.md` → Tech Lead อ่านมัน
2. Tech Lead เขียน `ARCHITECTURE.md` → Frontend Dev อ่านมัน
3. Frontend Dev เขียนโค้ดใน `src/` → QA Tester อ่านโค้ด

---

## การทำงานจริง (Example)

### Input: User ขอทำ Todo App

```yaml
# projects/inbox/request-001.yaml
type: web_fullstack
title: "Todo App with React"
description: "สร้าง Todo List ที่มี CRUD, filter, search"
```

### Workflow Execution:

#### Stage 1: PM Agent
```python
# PM Agent ได้รับ task
task = {
    'type': 'analyze_requirements',
    'input': 'request-001.yaml'
}

# PM Agent คิด
pm_thought = """
ผมได้รับงานสร้าง Todo App ให้วิเคราะห์ requirement:
- Feature: CRUD todos, filter, search
- Tech stack: React (frontend)
- ต้องการ backend? → ควรมี (เก็บ persistent data)
- Database? → SQLite หรือ PostgreSQL
- Auth? → ไม่ระบุ → ถาม user
"""

# PM Agent ตัดสินใจ
pm_action = "ask_user" # เพราะ requirement ไม่ชัด

# PM Agent ถามกลับ
pm_question = {
    'question': 'ต้องการ user authentication หรือไม่?',
    'options': ['ไม่ต้องการ (simple)', 'ต้องการ (with login)']
}

# User ตอบ: "ไม่ต้องการ"

# PM Agent ทำงานต่อ
pm_output = create_file('SPEC.md', content="""
# Todo App Specification

## Features
- Create todo
- Read todos (list + detail)
- Update todo (mark done, edit text)
- Delete todo
- Filter (all/active/completed)
- Search by text

## Tech Stack
- Frontend: React + Vite + TailwindCSS
- Backend: Node.js + Express
- Database: SQLite
- No authentication (public access)

## Success Criteria
- All CRUD operations work
- Filter & search are instant
- Mobile responsive
- Accessible (ARIA)
""")

# PM แจ้ง tech_lead
notify('tech_lead', 'SPEC.md is ready')
```

#### Stage 2: Tech Lead Agent
```python
# Tech Lead อ่าน SPEC.md
spec = read_file('SPEC.md')

# Tech Lead ออกแบบ
architecture = design_architecture(spec)

# Tech Lead เขียน
create_file('ARCHITECTURE.md', content="""
# System Architecture

## Directory Structure
```
todo-app/
├── frontend/           # React app
│   ├── src/
│   │   ├── components/
│   │   │   ├── TodoList.jsx
│   │   │   ├── TodoItem.jsx
│   │   │   ├── TodoForm.jsx
│   │   │   └── FilterBar.jsx
│   │   ├── hooks/
│   │   │   └── useTodos.js
│   │   └── api/
│   │       └── todos.js
│   └── package.json
└── backend/            # Express API
    ├── src/
    │   ├── routes/
    │   │   └── todos.js
    │   ├── db.js
    │   └── app.js
    └── package.json
```

## API Design
- GET /api/todos → List all
- POST /api/todos → Create
- PUT /api/todos/:id → Update
- DELETE /api/todos/:id → Delete

## Database Schema
```sql
CREATE TABLE todos (
    id INTEGER PRIMARY KEY,
    text TEXT NOT NULL,
    completed BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
""")

# สร้าง task breakdown
create_file('TASKS.md', content="""
# Tasks

## Frontend
- [ ] frontend/setup: Init React + Vite + Tailwind
- [ ] frontend/components: TodoList, TodoItem, TodoForm
- [ ] frontend/state: useTodos hook
- [ ] frontend/api: API client
- [ ] frontend/filter: Filter & search logic

## Backend
- [ ] backend/setup: Init Express + SQLite
- [ ] backend/db: Database setup
- [ ] backend/routes: CRUD endpoints
- [ ] backend/cors: Enable CORS

## Testing
- [ ] test/frontend: Component tests
- [ ] test/backend: API tests
""")

notify('frontend_dev', 'ready')
notify('backend_dev', 'ready')
```

#### Stage 3: Frontend Dev & Backend Dev (Parallel)

```python
# Frontend Dev
frontend_result = frontend_agent.execute_task({
    'type': 'implement',
    'filter': 'frontend/*',
    'inputs': ['ARCHITECTURE.md', 'TASKS.md']
})

# Backend Dev
backend_result = backend_agent.execute_task({
    'type': 'implement',
    'filter': 'backend/*',
    'inputs': ['ARCHITECTURE.md', 'TASKS.md']
})

# รอจนทั้งสองเสร็จ
wait_for_completion([frontend_result, backend_result])
```

---

## สิ่งที่ต้องทำต่อไป

### ✅ ที่มีอยู่แล้ว:
- Agent configs (YAML)
- Orchestrator skeleton
- LLM Router
- Agent Runner (basic)

### ❌ ที่ต้องทำเพิ่ม:

1. **Intelligent Agent Core** (สมองจริง)
   - Agentic loop
   - Tool execution
   - Memory management

2. **Workflow Engine** (เชื่อมการทำงาน)
   - Stage management
   - Conditional execution
   - Parallel execution

3. **State Management** (ติดตามสถานะ)
   - Project state tracking
   - Deliverables validation

4. **Communication Protocol** (ส่งต่องาน)
   - File-based messaging
   - Event notifications

5. **Testing & Validation** (ทดสอบ)
   - Unit tests for agents
   - Integration tests for workflows
   - End-to-end tests

---

## Next Steps

พร้อมเริ่มทำจริงไหมครับ? ผมแนะนำเริ่มแบบ step-by-step:

1. **Phase 1**: สร้าง IntelligentAgent class ที่ทำงานได้จริง
2. **Phase 2**: ทดสอบกับ PM agent (agent เดียว)
3. **Phase 3**: เชื่อม PM → Tech Lead (2 agents ทำงานต่อกัน)
4. **Phase 4**: เพิ่ม Frontend Dev
5. **Phase 5**: Full workflow

จะเริ่มจาก Phase 1 ไหมครับ?
