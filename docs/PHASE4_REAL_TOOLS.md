# Phase 4: Real Tools Integration ✅

## เป้าหมาย
ให้ agents มีความสามารถจริงๆ ในการทำงาน:
- ✅ Read/Write/Edit files
- ✅ Run bash commands
- ✅ Search code (Glob, Grep)
- ✅ Git operations

---

## Tools ที่สร้างเสร็จ

### 1. 📄 File Operations

#### ReadFileTool
```python
result = registry.execute_tool('read_file', path='SPEC.md')
# Returns: {'success': True, 'content': '...', 'lines': 50}
```

**ใช้เมื่อ:**
- อ่าน SPEC.md ที่ PM สร้าง
- อ่าน ARCHITECTURE.md
- อ่าน code ที่มีอยู่

#### WriteFileTool
```python
result = registry.execute_tool(
    'write_file',
    path='src/App.jsx',
    content='import React from "react"...'
)
# Returns: {'success': True, 'path': '...', 'bytes_written': 1234}
```

**ใช้เมื่อ:**
- สร้างไฟล์ใหม่
- Overwrite ไฟล์เก่า

#### EditFileTool
```python
result = registry.execute_tool(
    'edit_file',
    path='package.json',
    old_text='"version": "1.0.0"',
    new_text='"version": "1.0.1"'
)
# Returns: {'success': True, 'replacements': 1}
```

**ใช้เมื่อ:**
- แก้ไขโค้ดบางส่วน
- Update config files

---

### 2. 🔍 Search Tools

#### GlobTool
```python
result = registry.execute_tool('glob', pattern='src/**/*.jsx')
# Returns: {'success': True, 'matches': ['src/App.jsx', ...], 'count': 5}
```

**ใช้เมื่อ:**
- หาไฟล์ที่มี pattern ตรงกัน
- List files in directory

**Patterns:**
- `*.py` - Python files in current dir
- `**/*.js` - All JS files recursively
- `src/components/*.tsx` - Specific path pattern

#### GrepTool
```python
result = registry.execute_tool('grep', pattern='import React', path='src')
# Returns: {
#   'success': True,
#   'matches': [
#     {'file': 'src/App.jsx', 'line': 1, 'text': 'import React from "react"'},
#     ...
#   ],
#   'total': 10
# }
```

**ใช้เมื่อ:**
- Search for specific text
- Find function/class definitions
- Check if something exists

---

### 3. 💻 Bash Tool

```python
result = registry.execute_tool('bash', command='npm install react')
# Returns: {'success': True, 'stdout': '...', 'stderr': '', 'returncode': 0}
```

**Safety Features:**
- ⚠️ Whitelist of allowed commands
- ⏱️ 30 second timeout
- 🚫 Blocks dangerous commands

**Allowed commands (default):**
- `ls`, `cat`, `echo`, `mkdir`
- `npm`, `node`, `python`, `pytest`

**Blocked:**
- `rm -rf`
- Anything not in whitelist

**ใช้เมื่อ:**
- Install packages (`npm install`, `pip install`)
- Run tests (`pytest`, `npm test`)
- Build projects (`npm run build`)

---

### 4. 🔧 Git Tool

```python
# Git status
result = registry.execute_tool('git', operation='status')

# Git add
result = registry.execute_tool('git', operation='add', files=['src/'])

# Git commit
result = registry.execute_tool('git', operation='commit', message='Add new feature')

# Git diff
result = registry.execute_tool('git', operation='diff')
```

**Operations:**
- `status` - Show git status
- `diff` - Show changes
- `add` - Stage files
- `commit` - Create commit

**ใช้เมื่อ:**
- Check what changed
- Commit code
- Prepare for deployment

---

## ToolRegistry Architecture

### Class Structure

```python
class AgentTool:
    """Base class for all tools"""
    name: str
    description: str

    def execute(self, **kwargs) -> Dict
    def get_schema(self) -> Dict  # For LLM

class ToolRegistry:
    """Registry of available tools"""
    tools: Dict[str, AgentTool]

    def register(self, tool: AgentTool)
    def execute_tool(self, name: str, **params) -> Dict
    def get_tool_schemas(self) -> List[Dict]
```

### Registration

```python
# Create registry
registry = ToolRegistry(project_root)

# Register default tools
registry.register_default_tools()
# - ReadFileTool
# - WriteFileTool
# - EditFileTool
# - BashTool (with whitelist)
# - GlobTool
# - GrepTool
# - GitTool

# Register custom tools
registry.register(MyCustomTool())
```

---

## Integration with IntelligentAgent

### Before (Phase 1-3)
```python
agent = IntelligentAgent(
    agent_id='pm',
    config={...},
    llm_client=llm,
    tools={  # Simple dict
        'read_file': lambda path: ...,
        'write_file': lambda path, content: ...
    },
    project_root=Path('.')
)
```

### After (Phase 4)
```python
from core.agent_tools import create_tool_registry

# Create full-featured tool registry
registry = create_tool_registry(project_root)

agent = IntelligentAgent(
    agent_id='frontend_dev',
    config={...},
    llm_client=llm,
    tools=registry,  # Now has 7+ real tools!
    project_root=Path('.')
)
```

---

## Tool Schemas (for LLM)

Tools provide schemas that LLMs can understand:

```python
{
    'name': 'write_file',
    'description': 'Write content to a file (creates or overwrites)',
    'parameters': {
        'path': {
            'type': 'string',
            'description': 'Path to file (relative to project root)'
        },
        'content': {
            'type': 'string',
            'description': 'Content to write'
        }
    }
}
```

LLM sees this and knows how to use the tool!

---

## Real-World Example

### Scenario: Frontend Dev Agent creates React component

```python
# Agent thinks: "I need to create TodoList.jsx"

# 1. Check if file exists
result = tools.execute_tool('read_file', path='src/components/TodoList.jsx')
if not result['success']:
    # File doesn't exist, create it

# 2. Create component
component_code = """
import React from 'react';

function TodoList({ todos }) {
  return (
    <div className="todo-list">
      {todos.map(todo => (
        <div key={todo.id}>{todo.text}</div>
      ))}
    </div>
  );
}

export default TodoList;
"""

result = tools.execute_tool(
    'write_file',
    path='src/components/TodoList.jsx',
    content=component_code
)

# 3. Update index
result = tools.execute_tool(
    'edit_file',
    path='src/components/index.js',
    old_text='export { App };',
    new_text='export { App, TodoList };'
)

# 4. Install dependencies if needed
result = tools.execute_tool('bash', command='npm install')

# 5. Commit changes
tools.execute_tool('git', operation='add', files=['src/'])
tools.execute_tool('git', operation='commit', message='Add TodoList component')
```

---

## Testing

```bash
# Test all tools
python3 examples/test_agent_tools.py

# Test specific tool category
python3 examples/test_agent_tools.py --test file
python3 examples/test_agent_tools.py --test search
python3 examples/test_agent_tools.py --test bash
python3 examples/test_agent_tools.py --test git
```

### Test Results
```
✅ PASS - file_operations
✅ PASS - search_tools
✅ PASS - bash_tool
✅ PASS - git_tool

Overall: ✅ ALL TESTS PASSED
```

---

## Safety Considerations

### 1. File Operations
- ✅ Only access files within project_root
- ⚠️ Can overwrite files (by design)
- ⚠️ No size limits (yet)

### 2. Bash Commands
- ✅ Whitelist of allowed commands
- ✅ 30 second timeout
- ⚠️ Still powerful - use carefully

### 3. Git Operations
- ✅ Safe operations (no force push)
- ✅ Local only (no remote push by default)

---

## Next: Phase 5

จะเพิ่ม:
- Testing suite
- Error monitoring
- Performance optimization
- Cost tracking
- Production deployment guide

---

## สรุป Phase 4

✅ **สำเร็จ:**
1. AgentTool base class - extensible tool system
2. 7 real tools implemented:
   - ReadFileTool, WriteFileTool, EditFileTool
   - BashTool (with safety)
   - GlobTool, GrepTool
   - GitTool
3. ToolRegistry - manage tools
4. Integration with IntelligentAgent
5. Tool schemas for LLM
6. Comprehensive tests

🎯 **ผลลัพธ์:**
Agents can now DO real work:
- Create and edit files
- Run commands
- Search code
- Use Git

🚀 **พร้อมสำหรับ Phase 5:**
Production-ready polish!
