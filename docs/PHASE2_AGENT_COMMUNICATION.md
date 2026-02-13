# Phase 2: Agent Communication

## เป้าหมาย
ให้ agents สามารถส่งงานต่อกันได้ผ่านไฟล์

## แนวคิดหลัก

### 1. Agents สื่อสารผ่าน FILES ไม่ใช่การคุยโดยตรง

```
❌ Wrong way:
PM Agent: "Hey Tech Lead, I analyzed the requirements..."
Tech Lead: "Thanks! Let me think about architecture..."

✅ Right way:
PM Agent → creates SPEC.md
Tech Lead → reads SPEC.md → creates ARCHITECTURE.md
```

**ทำไม?**
- ✅ เก็บ history ได้ (มีไฟล์เป็นหลักฐาน)
- ✅ Human-readable (คนอ่านได้)
- ✅ Git-friendly (track changes ได้)
- ✅ Async (ไม่ต้องรอกันตลอด)

### 2. Sequential Execution

```
Stage 1: PM Agent
  Input: REQUEST.md
  Output: SPEC.md, TASKS.md
  ↓
Stage 2: Tech Lead Agent
  Input: SPEC.md, TASKS.md  (from PM)
  Output: ARCHITECTURE.md
  ↓
Stage 3: Frontend Dev Agent
  Input: ARCHITECTURE.md, TASKS.md
  Output: src/components/*.jsx
```

### 3. Agent Coordinator

ทำหน้าที่:
- ✅ Register agents
- ✅ Execute workflow stages
- ✅ Verify inputs exist before running agent
- ✅ Record handoffs (who → who, which files)
- ✅ Handle errors and needs_input

---

## สิ่งที่สร้างแล้ว

### 1. AgentCoordinator Class

```python
coordinator = AgentCoordinator(project_root)

# Register agents
coordinator.register_agent('pm', pm_agent)
coordinator.register_agent('tech_lead', tech_lead_agent)

# Execute workflow
result = coordinator.execute_workflow([
    {
        'agent': 'pm',
        'task': {
            'type': 'analyze_requirements',
            'inputs': ['REQUEST.md'],
            'expected_outputs': ['SPEC.md']
        }
    },
    {
        'agent': 'tech_lead',
        'task': {
            'type': 'design_architecture',
            'inputs': ['SPEC.md'],  # From PM
            'expected_outputs': ['ARCHITECTURE.md']
        },
        'wait_for': ['pm']  # Don't start until PM done
    }
])
```

### 2. Workflow Definitions

**SIMPLE_WORKFLOW** - PM → Tech Lead
```python
SIMPLE_WORKFLOW = [
    {'agent': 'pm', 'task': {...}},
    {'agent': 'tech_lead', 'task': {...}, 'wait_for': ['pm']}
]
```

**FULL_DEV_WORKFLOW** - Complete dev team
```python
FULL_DEV_WORKFLOW = [
    {'agent': 'pm', ...},
    {'agent': 'tech_lead', ..., 'wait_for': ['pm']},
    {'agent': 'frontend_dev', ..., 'wait_for': ['tech_lead']},
    {'agent': 'qa_tester', ..., 'wait_for': ['frontend_dev']}
]
```

### 3. Handoff Mechanism

```python
@dataclass
class AgentHandoff:
    from_agent: str
    to_agent: str
    trigger: str  # 'completion', 'file_created', 'manual'
    files_to_pass: List[str]
    timestamp: str
```

---

## การทำงานจริง

### Example: Todo App Development

**Stage 1: PM Agent**
```
Input: REQUEST.md
"Build a todo app with React..."

Process:
1. Think: Analyze requirements
2. Act: Create SPEC.md with detailed specification
3. Evaluate: SPEC.md created? Yes → Complete

Output: SPEC.md
```

**Stage 2: Tech Lead Agent**
```
Input: SPEC.md (from PM)

Process:
1. Think: Read SPEC.md, understand requirements
2. Act: Design architecture, create ARCHITECTURE.md
3. Evaluate: ARCHITECTURE.md created? Yes → Complete

Output: ARCHITECTURE.md
```

**Coordinator Flow:**
```
1. Execute PM Agent
   ✅ PM creates SPEC.md

2. Record handoff: PM → Tech Lead
   Files: [SPEC.md]

3. Verify handoff: SPEC.md exists? ✅

4. Execute Tech Lead Agent
   ✅ Tech Lead creates ARCHITECTURE.md

5. Workflow complete!
```

---

## Key Improvements to IntelligentAgent

### Better File Creation

**Before:**
```python
CREATE_FILE: SPEC.md | Some content here
```
(Limited to one line, hard to create complex documents)

**After:**
```python
CREATE_FILE: SPEC.md
---CONTENT---
# Todo App Specification

## Features
- Add todo
- Mark complete
- Delete todo

## Technical Requirements
- React + Vite
- TailwindCSS
- localStorage for data
---END---
```
(Multi-line content, properly formatted)

### Better Action Parsing

- ✅ Handles multi-line content
- ✅ Parses LLM responses naturally
- ✅ Robust error handling

---

## Testing

### Test 1: Simple Handoff
```bash
python3 examples/test_agent_communication.py --mode simple
```

Verifies:
- ✅ Coordinator can track handoffs
- ✅ File verification works

### Test 2: Full PM → Tech Lead
```bash
python3 examples/test_agent_communication.py --mode full
```

Verifies:
- ✅ PM agent creates SPEC.md
- ✅ Tech Lead reads SPEC.md
- ✅ Tech Lead creates ARCHITECTURE.md
- ✅ Agents communicate successfully

---

## Next: Phase 3

จะเพิ่ม:
- Parallel execution (multiple agents at once)
- Approval gates (ask user before proceeding)
- Error recovery
- Conditional workflows

---

## สรุป Phase 2

✅ **สำเร็จ:**
1. AgentCoordinator - ควบคุม multi-agent workflows
2. File-based communication - agents ส่งงานผ่านไฟล์
3. Sequential execution - PM → Tech Lead
4. Handoff tracking - รู้ว่าใครส่งอะไรให้ใคร
5. Improved file creation - agents สร้างไฟล์ได้ดีขึ้น

🎯 **ผลลัพธ์:**
Agents สามารถทำงานร่วมกันได้แบบต่อเนื่อง!

🚀 **พร้อมสำหรับ Phase 3:**
Workflow Engine with parallel execution & approval gates
