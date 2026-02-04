#!/usr/bin/env python3
"""
Memory Manager for WitMind.AI Platform
Manages agent memories and project context
"""

import os
import json
import yaml
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any


class MemoryManager:
    """Manages agent memories and project context."""

    def __init__(self, root_path: str):
        self.root = Path(root_path)
        self.templates_path = self.root / 'shared' / 'templates'

    # =========================================================================
    # Project Setup
    # =========================================================================

    def init_project(self, project_id: str, project_name: str) -> Path:
        """Initialize a new project with memory and context folders."""
        project_path = self.root / 'projects' / 'active' / project_id

        # Create directories
        (project_path / '.context').mkdir(parents=True, exist_ok=True)
        (project_path / '.memory').mkdir(parents=True, exist_ok=True)
        (project_path / 'docs').mkdir(parents=True, exist_ok=True)
        (project_path / 'src').mkdir(parents=True, exist_ok=True)
        (project_path / 'tests').mkdir(parents=True, exist_ok=True)
        (project_path / 'assets').mkdir(parents=True, exist_ok=True)

        # Create initial context
        self._create_initial_context(project_path, project_id, project_name)

        return project_path

    def _create_initial_context(self, project_path: Path, project_id: str, project_name: str):
        """Create initial context files from templates."""
        context_path = project_path / '.context'

        # Create project_context.yaml
        context_file = context_path / 'project_context.yaml'
        if not context_file.exists():
            context = {
                'project': {
                    'id': project_id,
                    'name': project_name,
                    'type': None,
                },
                'client': {
                    'name': None,
                    'preferences': [],
                },
                'constraints': {
                    'budget': None,
                    'timeline': None,
                },
                'notes': {
                    'important': '',
                    'gotchas': '',
                }
            }
            with open(context_file, 'w', encoding='utf-8') as f:
                yaml.dump(context, f, allow_unicode=True, default_flow_style=False)

        # Create decisions_log.md
        decisions_file = context_path / 'decisions_log.md'
        if not decisions_file.exists():
            content = f"""# {project_name} - Decisions Log

> บันทึกการตัดสินใจสำคัญของโปรเจค

---

## Quick Reference

| ID | Decision | Date | By | Impact |
|----|----------|------|-----|--------|
| - | - | - | - | - |

---

## Decisions

(ยังไม่มีการตัดสินใจ)
"""
            decisions_file.write_text(content, encoding='utf-8')

        # Create handoff_notes.md
        handoff_file = context_path / 'handoff_notes.md'
        if not handoff_file.exists():
            content = f"""# {project_name} - Handoff Notes

> Notes สำหรับส่งต่อระหว่าง Stages

---

## Latest Handoff

(ยังไม่มี handoff)
"""
            handoff_file.write_text(content, encoding='utf-8')

    # =========================================================================
    # Agent Memory
    # =========================================================================

    def init_agent_memory(self, project_path: Path, agent_id: str, agent_name: str) -> Dict:
        """Initialize memory for an agent in a project."""
        memory_path = project_path / '.memory' / f'{agent_id}.json'

        if memory_path.exists():
            return self.load_agent_memory(project_path, agent_id)

        memory = {
            'agent_id': agent_id,
            'agent_name': agent_name,
            'project_id': project_path.name,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'context': {
                'role_in_project': '',
                'assigned_tasks': [],
                'completed_tasks': [],
            },
            'decisions': [],
            'learnings': [],
            'preferences': {},
            'todos': [],
            'blockers': [],
            'handoff_notes': {
                'for_next_agent': '',
                'assumptions_made': [],
                'warnings': [],
            }
        }

        self.save_agent_memory(project_path, agent_id, memory)
        return memory

    def load_agent_memory(self, project_path: Path, agent_id: str) -> Optional[Dict]:
        """Load agent memory from file."""
        memory_path = project_path / '.memory' / f'{agent_id}.json'

        if not memory_path.exists():
            return None

        with open(memory_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_agent_memory(self, project_path: Path, agent_id: str, memory: Dict):
        """Save agent memory to file."""
        memory_path = project_path / '.memory' / f'{agent_id}.json'
        memory['updated_at'] = datetime.now().isoformat()

        with open(memory_path, 'w', encoding='utf-8') as f:
            json.dump(memory, f, indent=2, ensure_ascii=False)

    def add_decision(self, project_path: Path, agent_id: str,
                     topic: str, decision: str, reasoning: str,
                     options: List[Dict] = None, impact: str = None):
        """Add a decision to agent memory."""
        memory = self.load_agent_memory(project_path, agent_id)
        if not memory:
            return

        decision_id = f"DEC-{len(memory['decisions']) + 1:03d}"
        decision_entry = {
            'id': decision_id,
            'date': datetime.now().isoformat(),
            'topic': topic,
            'options_considered': options or [],
            'decision': decision,
            'reasoning': reasoning,
            'impact': impact or '',
        }

        memory['decisions'].append(decision_entry)
        self.save_agent_memory(project_path, agent_id, memory)

        # Also update decisions log
        self._update_decisions_log(project_path, agent_id, decision_entry)

    def add_learning(self, project_path: Path, agent_id: str,
                     issue: str, solution: str, lesson: str,
                     category: str = 'general', files: List[str] = None):
        """Add a learning to agent memory."""
        memory = self.load_agent_memory(project_path, agent_id)
        if not memory:
            return

        learning_id = f"LRN-{len(memory['learnings']) + 1:03d}"
        learning_entry = {
            'id': learning_id,
            'date': datetime.now().isoformat(),
            'category': category,
            'issue': issue,
            'solution': solution,
            'files_affected': files or [],
            'lesson': lesson,
        }

        memory['learnings'].append(learning_entry)
        self.save_agent_memory(project_path, agent_id, memory)

    def _update_decisions_log(self, project_path: Path, agent_id: str, decision: Dict):
        """Update the project decisions log."""
        decisions_file = project_path / '.context' / 'decisions_log.md'

        if not decisions_file.exists():
            return

        content = decisions_file.read_text(encoding='utf-8')

        # Add to quick reference table
        new_row = f"| {decision['id']} | {decision['topic']} | {decision['date'][:10]} | {agent_id} | - |"

        # Add full decision entry
        new_entry = f"""

---

## {decision['id']}: {decision['topic']}

**Date:** {decision['date'][:10]}
**Made by:** {agent_id}

### Decision
{decision['decision']}

### Reasoning
{decision['reasoning']}

### Impact
{decision['impact'] or 'N/A'}
"""

        # Insert new content
        content = content.replace(
            "| - | - | - | - | - |",
            f"{new_row}\n| - | - | - | - | - |"
        )
        content += new_entry

        decisions_file.write_text(content, encoding='utf-8')

    # =========================================================================
    # Context Management
    # =========================================================================

    def load_project_context(self, project_path: Path) -> Optional[Dict]:
        """Load project context."""
        context_file = project_path / '.context' / 'project_context.yaml'

        if not context_file.exists():
            return None

        with open(context_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def update_project_context(self, project_path: Path, updates: Dict):
        """Update project context with new values."""
        context = self.load_project_context(project_path) or {}

        def deep_update(d, u):
            for k, v in u.items():
                if isinstance(v, dict):
                    d[k] = deep_update(d.get(k, {}), v)
                else:
                    d[k] = v
            return d

        context = deep_update(context, updates)

        context_file = project_path / '.context' / 'project_context.yaml'
        with open(context_file, 'w', encoding='utf-8') as f:
            yaml.dump(context, f, allow_unicode=True, default_flow_style=False)

    # =========================================================================
    # Handoff Management
    # =========================================================================

    def create_handoff(self, project_path: Path, from_agent: str, to_stage: str,
                       summary: str, tasks_done: List[str], priority_tasks: List[str],
                       assumptions: List[str] = None, warnings: List[str] = None):
        """Create a handoff note when transitioning between stages."""
        handoff_file = project_path / '.context' / 'handoff_notes.md'

        handoff_content = f"""
---

## Handoff: {from_agent} → {to_stage}

**Date:** {datetime.now().isoformat()[:10]}
**From:** {from_agent}
**To:** {to_stage}

### Summary
{summary}

### Work Completed
{chr(10).join(f'- [x] {task}' for task in tasks_done)}

### Priority Tasks for {to_stage}
{chr(10).join(f'1. {task}' for task in priority_tasks)}

### Assumptions Made
{chr(10).join(f'- {a}' for a in (assumptions or ['None'])) }

### Warnings
{chr(10).join(f'- ⚠️ {w}' for w in (warnings or ['None']))}

"""

        # Append to existing file
        existing = handoff_file.read_text(encoding='utf-8') if handoff_file.exists() else ''
        handoff_file.write_text(existing + handoff_content, encoding='utf-8')

        # Also update agent memory
        memory = self.load_agent_memory(project_path, from_agent)
        if memory:
            memory['handoff_notes'] = {
                'for_next_agent': summary,
                'assumptions_made': assumptions or [],
                'warnings': warnings or [],
            }
            self.save_agent_memory(project_path, from_agent, memory)

    # =========================================================================
    # Skill Loading
    # =========================================================================

    def get_skills_for_agent(self, agent_id: str, project_context: Dict = None) -> List[Path]:
        """Get relevant skill files for an agent based on context."""
        skills_path = self.root / 'shared' / 'skills'
        relevant_skills = []

        # Agent to skill mapping
        agent_skills_map = {
            'frontend_dev': ['coding/react', 'coding/nextjs'],
            'backend_dev': ['coding/python-fastapi', 'coding/nextjs'],
            'fullstack_dev': ['coding/react', 'coding/nextjs', 'coding/python-fastapi'],
            'devops': ['devops/docker', 'devops/ci-cd'],
            'qa_tester': ['testing'],
        }

        # Get base skills for agent
        skill_paths = agent_skills_map.get(agent_id, [])

        for skill_path in skill_paths:
            full_path = skills_path / skill_path
            if full_path.exists():
                relevant_skills.append(full_path)

        # Add context-specific skills
        if project_context:
            tech_stack = project_context.get('tech_stack', {})
            if tech_stack.get('frontend') == 'nextjs':
                nextjs_path = skills_path / 'coding' / 'nextjs'
                if nextjs_path.exists() and nextjs_path not in relevant_skills:
                    relevant_skills.append(nextjs_path)

        return relevant_skills

    def load_skill(self, skill_path: Path) -> Optional[Dict]:
        """Load a skill configuration."""
        skill_file = skill_path / 'skill.yaml'

        if not skill_file.exists():
            return None

        with open(skill_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)


# Singleton instance
_memory_manager = None


def get_memory_manager(root_path: str = None) -> MemoryManager:
    """Get or create the memory manager instance."""
    global _memory_manager
    if _memory_manager is None:
        if root_path is None:
            root_path = os.environ.get('WITMIND_ROOT', '/home/wit/6amdev')
        _memory_manager = MemoryManager(root_path)
    return _memory_manager
