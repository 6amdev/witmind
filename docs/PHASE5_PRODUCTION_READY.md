# Phase 5: Production Ready ✅

## เป้าหมาย
ทำให้ Witmind พร้อมใช้งานจริงในระดับ Production

---

## สิ่งที่เพิ่มเข้ามา

### 1. 📊 Monitoring & Metrics

#### MetricsCollector
```python
from core.monitoring import MetricsCollector, track_execution

collector = MetricsCollector(Path('metrics'))

with track_execution('pm', 'analyze', collector) as tracker:
    # Do work
    tracker.record_llm_call(tokens_in=1000, tokens_out=500)
    tracker.record_tool_call('read_file')
    tracker.add_deliverable('SPEC.md')
    tracker.set_success(True)

# Get summary
summary = collector.get_summary()
print(f"Total cost: ${summary['total_cost_usd']}")
print(f"Success rate: {summary['successful']}/{summary['total_executions']}")
```

**Tracks:**
- ⏱️ Execution time
- 💰 Cost (LLM tokens)
- 🔧 Tool usage
- ✅ Success/failure
- 📄 Deliverables

#### CostTracker
```python
from core.monitoring import CostTracker

cost = CostTracker.calculate_cost(
    model='claude-sonnet-4',
    tokens_input=1000,
    tokens_output=500
)
print(f"Cost: ${cost:.4f}")
```

**Pricing Database:**
| Model | Input (per 1M) | Output (per 1M) |
|-------|---------------|-----------------|
| Claude Sonnet 4 | $3.00 | $15.00 |
| Claude Haiku 4 | $0.25 | $1.25 |
| Gemini Flash (OpenRouter) | **FREE** | **FREE** |
| Ollama | **FREE** | **FREE** |

---

### 2. 🛡️ Error Handling

#### Custom Exceptions
```python
from core.error_handling import (
    AgentError,
    ToolError,
    LLMError,
    WorkflowError,
    ValidationError
)

# Raise specific errors
if not agent:
    raise AgentError(f"Agent {agent_id} not found")

if tool_result.get('error'):
    raise ToolError(f"Tool {tool_name} failed: {error}")
```

#### Retry Decorator
```python
from core.error_handling import retry_on_error

@retry_on_error(max_retries=3, delay=1.0, backoff=2.0)
def call_llm_api():
    # Might fail due to network issues
    return llm.chat(...)

result = call_llm_api()  # Auto-retries on failure
```

#### Error Messages
```python
from core.error_handling import ErrorMessages

# User-friendly error messages
print(ErrorMessages.llm_api_error('claude', 'API key invalid'))
print(ErrorMessages.tool_error('write_file', 'Permission denied'))
print(ErrorMessages.agent_timeout('pm', 300))
```

#### Validation
```python
from core.error_handling import validate_task, validate_file_path

# Validate before execution
validate_task(task)  # Raises ValidationError if invalid
validate_file_path('../../etc/passwd', project_root)  # Blocks path traversal
```

---

### 3. 📝 Structured Logging

```python
from core.monitoring import setup_production_logging, StructuredLogger

# Setup logging
log_dir = setup_production_logging(Path('logs'))
# Creates:
#   - logs/app.log (all logs)
#   - logs/errors.log (errors only)
#   - logs/metrics/ (metrics files)

# Use structured logger
logger = StructuredLogger('witmind', log_dir / 'app.log')

logger.log_agent_start('pm', task)
logger.log_tool_call('read_file', success=True)
logger.log_agent_complete('pm', success=True, duration=12.5)
logger.log_error('Something failed', context={'agent': 'pm'})
```

**Log Format:**
```
2026-02-13 19:45:23 - witmind - INFO - Agent pm started
2026-02-13 19:45:25 - witmind - DEBUG - Tool read_file called
2026-02-13 19:45:35 - witmind - INFO - Agent pm completed
2026-02-13 19:45:35 - witmind - ERROR - LLM API error: rate limit exceeded
```

---

## Production Deployment Guide

### 1. Environment Setup

```bash
# 1. Clone repository
git clone https://github.com/6amdev/witmind.git
cd witmind

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r platform/requirements.txt
pip install anthropic httpx pyyaml  # Core deps

# 4. Configure environment
cp .env.example ~/.env
nano ~/.env  # Add API keys
```

### 2. Configuration

```bash
# ~/.env
ANTHROPIC_API_KEY=sk-ant-xxx  # Or leave empty if using OpenRouter
OPENROUTER_API_KEY=sk-or-xxx  # Recommended!

# Logging
LOG_LEVEL=INFO
LOG_DIR=~/witmind-data/logs

# Monitoring
METRICS_DIR=~/witmind-data/metrics
ENABLE_COST_TRACKING=true

# Safety
MAX_AGENT_ITERATIONS=10
AGENT_TIMEOUT_SECONDS=300
```

### 3. Directory Structure

```
~/witmind-data/
├── projects/              # Active projects
│   ├── inbox/            # New requests
│   ├── active/           # In progress
│   ├── review/           # Needs review
│   └── completed/        # Done
├── logs/                 # Application logs
│   ├── app.log
│   ├── errors.log
│   └── metrics/
└── cache/                # Temp files
```

### 4. Running in Production

```python
#!/usr/bin/env python3
"""Production runner"""

from pathlib import Path
from core.monitoring import setup_production_logging, MetricsCollector
from core.workflow_engine import WorkflowEngine
from core.agent_tools import create_tool_registry
from core.llm_client import create_llm_client
from core.intelligent_agent import create_intelligent_agent

# Setup
log_dir = Path('~/witmind-data/logs').expanduser()
setup_production_logging(log_dir)

metrics_dir = Path('~/witmind-data/metrics').expanduser()
collector = MetricsCollector(metrics_dir)

# Create project
project_root = Path('~/witmind-data/projects/active/proj-001').expanduser()
project_root.mkdir(parents=True, exist_ok=True)

# Setup tools
tools = create_tool_registry(project_root)

# Setup LLM (OpenRouter recommended for production)
llm = create_llm_client('openrouter', model='anthropic/claude-3.5-sonnet')

# Create agents
pm = create_intelligent_agent('pm', 'dev', pm_config, llm, project_root, tools)
tech_lead = create_intelligent_agent('tech_lead', 'dev', tl_config, llm, project_root, tools)

# Run workflow
engine = WorkflowEngine(project_root)
engine.register_agent('pm', pm)
engine.register_agent('tech_lead', tech_lead)

result = engine.execute()

# Show results
print(f"Success: {result['success']}")
print(f"Cost: ${collector.get_summary()['total_cost_usd']}")
```

---

## Best Practices

### 1. Cost Optimization

✅ **Use cheaper models for simple tasks:**
```python
# PM, Tech Lead: Use Sonnet (smart, expensive)
llm_smart = create_llm_client('openrouter', model='anthropic/claude-3.5-sonnet')

# QA, DevOps: Use Haiku (fast, cheap)
llm_fast = create_llm_client('openrouter', model='anthropic/claude-3-haiku')

# Testing: Use Gemini Flash (FREE!)
llm_free = create_llm_client('openrouter', model='google/gemini-flash-1.5')
```

✅ **Track costs:**
```python
with track_execution('pm', 'analyze', collector) as tracker:
    # Costs automatically tracked
    pass

summary = collector.get_summary()
if summary['total_cost_usd'] > 1.0:
    print("⚠️ High cost alert!")
```

### 2. Error Handling

✅ **Always use try-except:**
```python
try:
    result = agent.execute_task(task)
except AgentError as e:
    logger.error(f"Agent failed: {e}")
    # Handle gracefully
except LLMError as e:
    logger.error(f"LLM failed: {e}")
    # Maybe retry or use fallback
```

✅ **Validate inputs:**
```python
from core.error_handling import validate_task

validate_task(task)  # Before execution
```

✅ **Use retry for network operations:**
```python
@retry_on_error(max_retries=3)
def call_api():
    return llm.chat(...)
```

### 3. Monitoring

✅ **Always collect metrics:**
```python
collector = MetricsCollector(metrics_dir)

# Track everything
with track_execution('agent_id', 'task_type', collector) as tracker:
    ...
```

✅ **Check metrics regularly:**
```bash
# Daily cost report
python3 scripts/daily_cost_report.py

# Performance report
python3 scripts/performance_report.py
```

✅ **Set up alerts:**
```python
summary = collector.get_summary()

if summary['total_cost_usd'] > 10.0:
    send_alert("Daily cost exceeded $10!")

if summary['failed'] > summary['successful']:
    send_alert("More failures than successes!")
```

### 4. Security

✅ **Never commit .env:**
```bash
# .gitignore
.env
*.key
credentials.json
```

✅ **Validate file paths:**
```python
validate_file_path(path, project_root)  # Prevent path traversal
```

✅ **Whitelist bash commands:**
```python
BashTool(
    project_root,
    allowed_commands=['npm', 'pytest', 'ls']  # Only safe commands
)
```

---

## Monitoring Dashboard (Optional)

```python
# scripts/dashboard.py
"""Simple metrics dashboard"""

from core.monitoring import MetricsCollector

collector = MetricsCollector(Path('metrics'))
summary = collector.get_summary()

print(f"""
╔══════════════════════════════════════╗
║      WITMIND METRICS DASHBOARD       ║
╠══════════════════════════════════════╣
║ Total Executions: {summary['total_executions']:>18} ║
║ Successful:       {summary['successful']:>18} ║
║ Failed:           {summary['failed']:>18} ║
╠══════════════════════════════════════╣
║ Total Cost:       ${summary['total_cost_usd']:>17.4f} ║
║ Avg per Run:      ${summary['avg_cost_per_execution']:>17.4f} ║
╠══════════════════════════════════════╣
║ Total Time:       {summary['total_duration_seconds']:>15.2f}s ║
║ Avg per Run:      {summary['avg_duration_seconds']:>15.2f}s ║
╚══════════════════════════════════════╝
""")
```

---

## Testing

```bash
# Run all tests
pytest tests/

# Test with monitoring
python3 examples/test_with_monitoring.py

# Load test
python3 tests/load_test.py --agents 10 --duration 60
```

---

## Troubleshooting

### High Costs
```bash
# 1. Check which agents are expensive
python3 scripts/cost_breakdown.py

# 2. Switch to cheaper models
# 3. Reduce max_iterations
# 4. Use caching
```

### Slow Execution
```bash
# 1. Check bottlenecks
python3 scripts/performance_analysis.py

# 2. Enable parallel execution
# 3. Use faster models (Haiku vs Sonnet)
# 4. Reduce iterations
```

### Frequent Failures
```bash
# 1. Check error logs
tail -f logs/errors.log

# 2. Add more retries
# 3. Improve prompts
# 4. Validate inputs better
```

---

## สรุป Phase 5

✅ **สำเร็จ:**
1. Monitoring & Metrics - track everything
2. Cost Tracking - know what you're spending
3. Error Handling - robust & user-friendly
4. Structured Logging - production-grade
5. Validation - prevent bad inputs
6. Retry Logic - handle transient errors
7. Production Deployment Guide
8. Best Practices Documentation

🎯 **ผลลัพธ์:**
Witmind is now PRODUCTION READY!
- ✅ Observable (metrics, logs)
- ✅ Reliable (error handling, retries)
- ✅ Cost-efficient (tracking, optimization)
- ✅ Secure (validation, whitelists)
- ✅ Maintainable (structured logs)

---

## 🎉 WITMIND COMPLETE - 100%!

All 5 Phases Done:
1. ✅ Intelligent Agent Core
2. ✅ Agent Communication
3. ✅ Workflow Engine
4. ✅ Real Tools Integration
5. ✅ Production Ready

**Ready for real-world use!** 🚀
