## Phase 3: Workflow Engine ✅

## เป้าหมาย
ควบคุมการทำงานของ agents แบบ advanced:
- Parallel execution
- Approval gates
- Conditional workflows
- Error recovery

---

## Key Features

### 1. 🔀 Parallel Execution

**ปัญหา:**
```
Sequential (slow):
PM (2 min) → Tech Lead (3 min) → Frontend (10 min) → Backend (10 min)
Total: 25 minutes
```

**แก้ไข:**
```
Parallel (fast):
PM (2 min) → Tech Lead (3 min) → [Frontend (10 min) + Backend (10 min)]
Total: 15 minutes (save 10 min!)
```

**ตัวอย่าง:**
```python
# Frontend และ Backend ทำงานพร้อมกัน
parallel_stages = create_parallel_stages(
    group_name='development',
    stages_config=[
        {'id': 'frontend_dev', 'agent': 'frontend_dev', ...},
        {'id': 'backend_dev', 'agent': 'backend_dev', ...}
    ]
)
```

### 2. 🔐 Approval Gates

**ทำไมต้องมี:**
- Agents ไม่ควรทำทุกอย่างอัตโนมัติ 100%
- บางขั้นตอนต้องถาม user ก่อน
- ตัวอย่าง: Deploy to production, Delete data, Spend money

**ตัวอย่าง:**
```python
create_stage(
    id='deploy_production',
    agent='devops',
    task={...},
    requires_approval=True,
    approval_message="Deploy to production? This will affect live users."
)
```

**การทำงาน:**
```
Workflow Engine: "Deploy to production? This will affect live users."
User: [Approve] or [Deny]

If Approve → Continue
If Deny → Skip stage
```

### 3. ⚙️ Conditional Execution

**ปัญหา:**
ไม่ใช่ทุก project ต้องทำทุกขั้นตอน
- Web app ไม่ต้องมี mobile dev
- Simple project ไม่ต้อง microservices

**แก้ไข:**
```python
def has_mobile_requirement(project_root):
    spec = (project_root / 'SPEC.md').read_text()
    return 'mobile' in spec.lower()

create_stage(
    id='mobile_dev',
    agent='mobile_dev',
    task={...},
    condition=has_mobile_requirement  # Skip if False
)
```

### 4. 🔄 Error Recovery

**Strategies:**

| Strategy | ทำอะไร | ใช้เมื่อ |
|----------|--------|----------|
| `stop` | หยุด workflow ทันที | Critical errors (default) |
| `skip` | ข้ามไป stage ถัดไป | Non-critical errors |
| `retry` | ลองใหม่ N ครั้ง | Network errors, timeouts |

**ตัวอย่าง:**
```python
create_stage(
    id='api_call',
    agent='backend_dev',
    task={...},
    on_error='retry',
    max_retries=3  # ลองใหม่ 3 ครั้ง
)
```

---

## Architecture

### WorkflowStage

```python
@dataclass
class WorkflowStage:
    id: str
    agent: str
    task: Dict
    status: StageStatus  # PENDING, RUNNING, COMPLETED, FAILED, SKIPPED

    # Dependencies
    wait_for: List[str]  # รอ stages ไหนให้เสร็จก่อน

    # Conditional
    condition: Callable  # ถ้า return False → skip

    # Approval
    requires_approval: bool
    approval_message: str

    # Error handling
    on_error: str  # 'stop', 'skip', 'retry'
    max_retries: int

    # Parallel
    can_run_parallel: bool
    parallel_group: str  # Stages in same group run together
```

### WorkflowEngine

```python
class WorkflowEngine:
    def execute(self, on_approval_needed=None):
        """Main execution loop"""
        while has_pending_stages:
            # 1. Find ready stages (deps met, condition True)
            ready = self._get_ready_stages()

            # 2. Group by parallel capability
            groups = self._group_parallel_stages(ready)

            # 3. Execute each group
            for group in groups:
                if len(group) > 1:
                    # Parallel
                    self._execute_parallel(group)
                else:
                    # Sequential
                    self._execute_stage(group[0])
```

---

## ตัวอย่างการใช้งาน

### Example 1: Simple Workflow with Approval

```python
from core.workflow_engine import WorkflowEngine, create_stage

engine = WorkflowEngine(project_root)
engine.register_agent('pm', pm_agent)
engine.register_agent('tech_lead', tech_lead_agent)

# Stage 1: PM (no approval)
engine.add_stage(create_stage(
    id='pm_analysis',
    agent='pm',
    task={'type': 'analyze', 'inputs': ['REQUEST.md']}
))

# Stage 2: Tech Lead (requires approval)
engine.add_stage(create_stage(
    id='tech_design',
    agent='tech_lead',
    task={'type': 'design', 'inputs': ['SPEC.md']},
    wait_for=['pm_analysis'],
    requires_approval=True,
    approval_message="Approve architecture design?"
))

# Execute
def approval_handler(stage, message):
    print(f"Approve: {message} (y/n)")
    return input().lower() == 'y'

result = engine.execute(on_approval_needed=approval_handler)
```

### Example 2: Parallel Development

```python
from core.workflow_engine import create_parallel_stages

# PM → Tech Lead (sequential)
engine.add_stage(create_stage('pm', 'pm', {...}))
engine.add_stage(create_stage('tech_lead', 'tech_lead', {...}, wait_for=['pm']))

# Frontend + Backend (parallel)
parallel = create_parallel_stages('development', [
    {'id': 'frontend', 'agent': 'frontend_dev', ...},
    {'id': 'backend', 'agent': 'backend_dev', ...}
])
for stage in parallel:
    stage.wait_for = ['tech_lead']
    engine.add_stage(stage)

# QA (wait for both)
engine.add_stage(create_stage(
    'qa', 'qa_tester', {...},
    wait_for=['frontend', 'backend']
))

result = engine.execute()
```

### Example 3: Conditional Workflow

```python
def needs_database(project_root):
    spec = (project_root / 'SPEC.md').read_text()
    return 'database' in spec.lower() or 'persistent' in spec.lower()

engine.add_stage(create_stage(
    id='database_setup',
    agent='backend_dev',
    task={'type': 'setup_database'},
    condition=needs_database  # Only run if needed
))
```

### Example 4: Error Recovery

```python
# Network call - retry on failure
engine.add_stage(create_stage(
    id='api_integration',
    agent='backend_dev',
    task={'type': 'integrate_api'},
    on_error='retry',
    max_retries=3
))

# Optional feature - skip on failure
engine.add_stage(create_stage(
    id='analytics',
    agent='backend_dev',
    task={'type': 'add_analytics'},
    on_error='skip'  # Not critical, skip if fails
))

# Critical task - stop on failure
engine.add_stage(create_stage(
    id='payment_integration',
    agent='backend_dev',
    task={'type': 'add_payment'},
    on_error='stop'  # Critical! Stop if fails (default)
))
```

---

## Execution Flow

```
1. Start workflow

2. Loop until all stages done:

   a. Get ready stages
      - Check dependencies (wait_for)
      - Check conditions
      - Filter by status (PENDING only)

   b. Group by parallel capability
      - Same parallel_group → run together
      - Different groups → run sequentially

   c. Execute group:
      If parallel:
        - Use ThreadPoolExecutor
        - Run all stages simultaneously
        - Wait for all to complete

      If sequential:
        - Run stage
        - Check if approval needed
        - Handle errors (stop/skip/retry)

   d. Update stage status
   e. Record results

3. Return results
```

---

## Benefits

### ⚡ Performance
- Parallel execution → faster workflows
- Skip unnecessary stages → save time

### 🎯 Control
- Approval gates → human oversight
- Conditional execution → flexible workflows

### 🛡️ Reliability
- Error recovery → handle failures gracefully
- Retry logic → resilience to transient errors

### 📊 Visibility
- Stage status tracking → know what's happening
- Detailed logging → debug easily

---

## Testing

```bash
# Test simple workflow
python3 examples/test_workflow_engine.py --test simple

# Test parallel execution
python3 examples/test_workflow_engine.py --test parallel

# Test approval gates
python3 examples/test_workflow_engine.py --test approval

# Test error handling
python3 examples/test_workflow_engine.py --test error

# Run all tests
python3 examples/test_workflow_engine.py --test all
```

---

## Next: Phase 4

จะเพิ่ม:
- Real tools integration (Read, Write, Edit, Bash)
- Web search capabilities
- Git operations
- File system operations

---

## สรุป Phase 3

✅ **สำเร็จ:**
1. WorkflowEngine - advanced orchestration
2. Parallel execution - run multiple agents at once
3. Approval gates - human-in-the-loop
4. Conditional workflows - skip unnecessary stages
5. Error recovery - handle failures gracefully

🎯 **ผลลัพธ์:**
- Workflows ยืดหยุ่นขึ้น
- เร็วขึ้น (parallel execution)
- ปลอดภัยขึ้น (approval gates)
- แข็งแรงขึ้น (error recovery)

🚀 **พร้อมสำหรับ Phase 4:**
Real tools integration for production use!
