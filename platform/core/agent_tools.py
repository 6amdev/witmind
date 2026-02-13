#!/usr/bin/env python3
"""
Agent Tools - Real tools that agents can use

These are the actual capabilities that make agents useful:
- Read/Write/Edit files
- Run commands
- Search code
- Web operations
- Git operations
"""

import os
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
import json

logger = logging.getLogger('agent_tools')


class AgentTool:
    """Base class for agent tools"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool"""
        raise NotImplementedError

    def get_schema(self) -> Dict:
        """Get tool schema for LLM"""
        return {
            'name': self.name,
            'description': self.description,
            'parameters': {}
        }


class ReadFileTool(AgentTool):
    """Read a file"""

    def __init__(self, project_root: Path):
        super().__init__(
            name='read_file',
            description='Read contents of a file'
        )
        self.project_root = project_root

    def execute(self, path: str, **kwargs) -> Dict:
        """Read file and return contents"""
        try:
            file_path = self.project_root / path
            if not file_path.exists():
                return {
                    'success': False,
                    'error': f'File not found: {path}'
                }

            content = file_path.read_text()
            return {
                'success': True,
                'content': content,
                'path': str(file_path),
                'lines': len(content.split('\n'))
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_schema(self) -> Dict:
        return {
            'name': self.name,
            'description': self.description,
            'parameters': {
                'path': {
                    'type': 'string',
                    'description': 'Path to file (relative to project root)'
                }
            }
        }


class WriteFileTool(AgentTool):
    """Write content to a file"""

    def __init__(self, project_root: Path):
        super().__init__(
            name='write_file',
            description='Write content to a file (creates or overwrites)'
        )
        self.project_root = project_root

    def execute(self, path: str, content: str, **kwargs) -> Dict:
        """Write content to file"""
        try:
            file_path = self.project_root / path

            # Create parent directories if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            file_path.write_text(content)

            return {
                'success': True,
                'path': str(file_path),
                'bytes_written': len(content.encode())
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_schema(self) -> Dict:
        return {
            'name': self.name,
            'description': self.description,
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


class EditFileTool(AgentTool):
    """Edit a file (find and replace)"""

    def __init__(self, project_root: Path):
        super().__init__(
            name='edit_file',
            description='Edit a file by finding and replacing text'
        )
        self.project_root = project_root

    def execute(self, path: str, old_text: str, new_text: str, **kwargs) -> Dict:
        """Find and replace text in file"""
        try:
            file_path = self.project_root / path

            if not file_path.exists():
                return {
                    'success': False,
                    'error': f'File not found: {path}'
                }

            # Read current content
            content = file_path.read_text()

            # Check if old_text exists
            if old_text not in content:
                return {
                    'success': False,
                    'error': f'Text not found in file: {old_text[:50]}...'
                }

            # Replace
            new_content = content.replace(old_text, new_text)

            # Write back
            file_path.write_text(new_content)

            return {
                'success': True,
                'path': str(file_path),
                'replacements': content.count(old_text)
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_schema(self) -> Dict:
        return {
            'name': self.name,
            'description': self.description,
            'parameters': {
                'path': {'type': 'string', 'description': 'File path'},
                'old_text': {'type': 'string', 'description': 'Text to find'},
                'new_text': {'type': 'string', 'description': 'Replacement text'}
            }
        }


class BashTool(AgentTool):
    """Run bash commands"""

    def __init__(self, project_root: Path, allowed_commands: Optional[List[str]] = None):
        super().__init__(
            name='bash',
            description='Run bash commands (use with caution!)'
        )
        self.project_root = project_root
        self.allowed_commands = allowed_commands  # Whitelist for safety

    def execute(self, command: str, **kwargs) -> Dict:
        """Run bash command"""
        try:
            # Safety check
            if self.allowed_commands:
                cmd_prefix = command.split()[0]
                if cmd_prefix not in self.allowed_commands:
                    return {
                        'success': False,
                        'error': f'Command not allowed: {cmd_prefix}'
                    }

            # Run command
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30
            )

            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Command timeout (30s)'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_schema(self) -> Dict:
        return {
            'name': self.name,
            'description': self.description,
            'parameters': {
                'command': {
                    'type': 'string',
                    'description': 'Bash command to run'
                }
            }
        }


class GlobTool(AgentTool):
    """Find files by pattern"""

    def __init__(self, project_root: Path):
        super().__init__(
            name='glob',
            description='Find files matching a pattern (e.g., "*.py", "src/**/*.js")'
        )
        self.project_root = project_root

    def execute(self, pattern: str, **kwargs) -> Dict:
        """Find files matching pattern"""
        try:
            matches = list(self.project_root.glob(pattern))
            files = [str(p.relative_to(self.project_root)) for p in matches if p.is_file()]

            return {
                'success': True,
                'pattern': pattern,
                'matches': files,
                'count': len(files)
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_schema(self) -> Dict:
        return {
            'name': self.name,
            'description': self.description,
            'parameters': {
                'pattern': {
                    'type': 'string',
                    'description': 'Glob pattern (e.g., "*.md", "src/**/*.py")'
                }
            }
        }


class GrepTool(AgentTool):
    """Search for text in files"""

    def __init__(self, project_root: Path):
        super().__init__(
            name='grep',
            description='Search for text in files'
        )
        self.project_root = project_root

    def execute(self, pattern: str, path: str = ".", **kwargs) -> Dict:
        """Search for pattern in files"""
        try:
            search_path = self.project_root / path
            matches = []

            if search_path.is_file():
                # Search single file
                content = search_path.read_text()
                for i, line in enumerate(content.split('\n'), 1):
                    if pattern in line:
                        matches.append({
                            'file': str(search_path.relative_to(self.project_root)),
                            'line': i,
                            'text': line.strip()
                        })
            else:
                # Search directory
                for file_path in search_path.rglob('*'):
                    if file_path.is_file() and not file_path.name.startswith('.'):
                        try:
                            content = file_path.read_text()
                            for i, line in enumerate(content.split('\n'), 1):
                                if pattern in line:
                                    matches.append({
                                        'file': str(file_path.relative_to(self.project_root)),
                                        'line': i,
                                        'text': line.strip()
                                    })
                        except:
                            # Skip binary files
                            pass

            return {
                'success': True,
                'pattern': pattern,
                'matches': matches[:50],  # Limit to 50 matches
                'total': len(matches)
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_schema(self) -> Dict:
        return {
            'name': self.name,
            'description': self.description,
            'parameters': {
                'pattern': {'type': 'string', 'description': 'Text to search for'},
                'path': {'type': 'string', 'description': 'Path to search in (default: ".")'}
            }
        }


class GitTool(AgentTool):
    """Git operations"""

    def __init__(self, project_root: Path):
        super().__init__(
            name='git',
            description='Git operations (status, diff, commit, etc.)'
        )
        self.project_root = project_root

    def execute(self, operation: str, **kwargs) -> Dict:
        """Execute git operation"""
        try:
            if operation == 'status':
                result = subprocess.run(
                    ['git', 'status', '--short'],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True
                )

            elif operation == 'diff':
                result = subprocess.run(
                    ['git', 'diff'],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True
                )

            elif operation == 'add':
                files = kwargs.get('files', ['.'])
                result = subprocess.run(
                    ['git', 'add'] + files,
                    cwd=self.project_root,
                    capture_output=True,
                    text=True
                )

            elif operation == 'commit':
                message = kwargs.get('message', 'Auto commit')
                result = subprocess.run(
                    ['git', 'commit', '-m', message],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True
                )

            else:
                return {
                    'success': False,
                    'error': f'Unknown git operation: {operation}'
                }

            return {
                'success': result.returncode == 0,
                'operation': operation,
                'output': result.stdout + result.stderr
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_schema(self) -> Dict:
        return {
            'name': self.name,
            'description': self.description,
            'parameters': {
                'operation': {
                    'type': 'string',
                    'description': 'Git operation: status, diff, add, commit'
                },
                'message': {
                    'type': 'string',
                    'description': 'Commit message (for commit operation)'
                },
                'files': {
                    'type': 'array',
                    'description': 'Files to add (for add operation)'
                }
            }
        }


class ToolRegistry:
    """Registry of available tools for agents"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.tools: Dict[str, AgentTool] = {}

    def register_default_tools(self):
        """Register all default tools"""
        self.register(ReadFileTool(self.project_root))
        self.register(WriteFileTool(self.project_root))
        self.register(EditFileTool(self.project_root))
        self.register(GlobTool(self.project_root))
        self.register(GrepTool(self.project_root))

        # Bash with safe whitelist
        self.register(BashTool(
            self.project_root,
            allowed_commands=['ls', 'cat', 'echo', 'mkdir', 'npm', 'node', 'python', 'pytest']
        ))

        # Git operations
        self.register(GitTool(self.project_root))

        logger.info(f"Registered {len(self.tools)} default tools")

    def register(self, tool: AgentTool):
        """Register a tool"""
        self.tools[tool.name] = tool
        logger.debug(f"Registered tool: {tool.name}")

    def get_tool(self, name: str) -> Optional[AgentTool]:
        """Get a tool by name"""
        return self.tools.get(name)

    def get_all_tools(self) -> Dict[str, AgentTool]:
        """Get all registered tools"""
        return self.tools

    def get_tool_schemas(self) -> List[Dict]:
        """Get schemas for all tools (for LLM)"""
        return [tool.get_schema() for tool in self.tools.values()]

    def execute_tool(self, tool_name: str, **params) -> Dict:
        """Execute a tool by name"""
        tool = self.get_tool(tool_name)
        if not tool:
            return {
                'success': False,
                'error': f'Tool not found: {tool_name}'
            }

        logger.info(f"Executing tool: {tool_name}")
        result = tool.execute(**params)
        logger.debug(f"Tool result: {result.get('success', False)}")

        return result


def create_tool_registry(project_root: Path, custom_tools: Optional[List[AgentTool]] = None) -> ToolRegistry:
    """
    Create a tool registry with default tools.

    Args:
        project_root: Project root directory
        custom_tools: Additional custom tools to register

    Returns:
        ToolRegistry instance
    """
    registry = ToolRegistry(project_root)
    registry.register_default_tools()

    if custom_tools:
        for tool in custom_tools:
            registry.register(tool)

    return registry
