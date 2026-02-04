"""
Agent Runner with LLM Router Support
Supports Claude Code, OpenRouter, and Ollama
"""

import os
import yaml
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

# Import LLM Router
try:
    from llm_router import LLMRouter, get_router
except ImportError:
    from core.llm_router import LLMRouter, get_router


class AgentRunner:
    """
    Runs agents using configurable LLM providers

    Usage:
        # Use default (Claude Code)
        runner = AgentRunner()

        # Use specific provider
        runner = AgentRunner(provider="ollama", model="llama3.1:70b")

        # Run agent
        result = runner.run_with_tools("backend_dev", "dev", "my-project")
    """

    def __init__(self,
                 provider: str = None,
                 model: str = None,
                 platform_path: str = None):
        """
        Initialize agent runner

        Args:
            provider: LLM provider (claude_code, openrouter, ollama)
            model: Model name
            platform_path: Path to 6amdev-platform
        """
        # Setup paths
        self.platform_path = Path(platform_path or os.environ.get(
            "PLATFORM_PATH",
            os.path.expanduser("~/workspace/6amdev-platform")
        ))

        # Initialize LLM Router
        if provider:
            self.llm = LLMRouter(provider=provider, model=model)
        else:
            # Try to load from config, fallback to auto-select
            config_path = self.platform_path / "config" / "llm.yaml"
            if config_path.exists():
                self.llm = LLMRouter.from_config_file(str(config_path))
            else:
                self.llm = LLMRouter.auto_select()

        print(f"Using LLM: {self.llm.provider_name} ({self.llm.config.get('model', 'default')})")

    def load_agent(self, agent_id: str, team_id: str = "dev") -> Dict[str, Any]:
        """Load agent configuration"""
        agent_path = self.platform_path / "teams" / team_id / "agents" / f"{agent_id}.yaml"

        if not agent_path.exists():
            raise FileNotFoundError(f"Agent not found: {agent_path}")

        with open(agent_path) as f:
            return yaml.safe_load(f)

    def load_project(self, project_id: str) -> Dict[str, Any]:
        """Load project configuration"""
        project_path = self.platform_path / "projects" / "active" / project_id / "PROJECT.yaml"

        if not project_path.exists():
            raise FileNotFoundError(f"Project not found: {project_path}")

        with open(project_path) as f:
            return yaml.safe_load(f)

    def build_prompt(self, agent_config: Dict, project_config: Dict) -> str:
        """Build prompt for agent"""
        agent = agent_config.get("agent", {})

        # Get agent role and capabilities
        role = agent.get("role", "Developer")
        capabilities = agent.get("capabilities", [])
        instructions = agent.get("instructions", {})

        # Get project info
        project = project_config.get("project", {})
        description = project.get("description", "")

        # Build system prompt
        prompt = f"""You are a {role} working on this project.

## Project
{description}

## Your Capabilities
{chr(10).join(f"- {c}" for c in capabilities)}

## Instructions
"""
        # Add task-specific instructions
        for task_type, task_instructions in instructions.items():
            if isinstance(task_instructions, list):
                prompt += f"\n### {task_type}\n"
                prompt += "\n".join(f"- {i}" for i in task_instructions)

        # Add output requirements
        outputs = agent.get("outputs", [])
        if outputs:
            prompt += f"\n\n## Expected Outputs\n"
            prompt += "\n".join(f"- {o}" for o in outputs)

        return prompt

    def run_with_tools(self,
                       agent_id: str,
                       team_id: str,
                       project_id: str,
                       **kwargs) -> Dict[str, Any]:
        """
        Run agent with tools enabled

        For Claude Code: Uses native tool support
        For OpenRouter/Ollama: Simulates via prompt engineering
        """
        try:
            # Load configs
            agent_config = self.load_agent(agent_id, team_id)
            project_config = self.load_project(project_id)
            project_path = self.platform_path / "projects" / "active" / project_id

            # Build prompt
            system_prompt = self.build_prompt(agent_config, project_config)

            # Provider-specific handling
            if self.llm.provider_name == "claude_code":
                return self._run_claude_code(
                    agent_id, system_prompt, project_path, kwargs
                )
            else:
                return self._run_api_provider(
                    agent_id, system_prompt, project_path, kwargs
                )

        except FileNotFoundError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _run_claude_code(self,
                         agent_id: str,
                         system_prompt: str,
                         project_path: Path,
                         kwargs: Dict) -> Dict[str, Any]:
        """Run using Claude Code CLI with native tools"""
        try:
            # Get allowed tools based on agent type
            allowed_tools = self._get_allowed_tools(agent_id)

            cmd = [
                "claude",
                "-p", f"Execute your role as defined. Work in: {project_path}",
                "--system", system_prompt,
                "--allowedTools", ",".join(allowed_tools),
                "--output-format", "json"
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=kwargs.get("timeout", 300),
                cwd=str(project_path)
            )

            if result.returncode == 0:
                return {
                    "success": True,
                    "output": result.stdout,
                    "agent": agent_id
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr or "Claude Code failed",
                    "agent": agent_id
                }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Agent timed out",
                "agent": agent_id
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "agent": agent_id
            }

    def _run_api_provider(self,
                          agent_id: str,
                          system_prompt: str,
                          project_path: Path,
                          kwargs: Dict) -> Dict[str, Any]:
        """
        Run using OpenRouter or Ollama API

        Since these don't have native tool support, we use a
        structured output approach
        """
        # Enhanced prompt for non-tool providers
        task_prompt = f"""Execute your role for the project.

Working Directory: {project_path}

IMPORTANT: Since you cannot directly execute tools, provide your output in this format:

## Analysis
[Your analysis of the task]

## Files to Create
For each file:
```filename: path/to/file.ext
[file contents]
```

## Commands to Run
```bash
[commands that should be executed]
```

## Summary
[Brief summary of what you produced]

Now, complete your assigned task.
"""

        result = self.llm.generate(
            prompt=task_prompt,
            system_prompt=system_prompt,
            timeout=kwargs.get("timeout", 300)
        )

        if result["success"]:
            # Parse and execute the response
            response = result["response"]
            execution_result = self._execute_structured_response(
                response, project_path
            )

            return {
                "success": True,
                "output": response,
                "execution": execution_result,
                "agent": agent_id,
                "provider": result.get("provider")
            }
        else:
            return {
                "success": False,
                "error": result["error"],
                "agent": agent_id
            }

    def _execute_structured_response(self,
                                      response: str,
                                      project_path: Path) -> Dict[str, Any]:
        """Parse and execute structured response from API providers"""
        import re

        results = {
            "files_created": [],
            "commands_executed": [],
            "errors": []
        }

        # Extract and create files
        file_pattern = r'```filename:\s*(.+?)\n(.*?)```'
        for match in re.finditer(file_pattern, response, re.DOTALL):
            filename = match.group(1).strip()
            content = match.group(2)

            try:
                file_path = project_path / filename
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content)
                results["files_created"].append(str(filename))
            except Exception as e:
                results["errors"].append(f"Failed to create {filename}: {e}")

        # Extract and run commands (safely)
        cmd_pattern = r'```bash\n(.*?)```'
        for match in re.finditer(cmd_pattern, response, re.DOTALL):
            commands = match.group(1).strip()

            # Only execute safe commands
            safe_commands = self._filter_safe_commands(commands)
            for cmd in safe_commands:
                try:
                    result = subprocess.run(
                        cmd,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=60,
                        cwd=str(project_path)
                    )
                    results["commands_executed"].append({
                        "command": cmd,
                        "success": result.returncode == 0,
                        "output": result.stdout[:500] if result.stdout else None
                    })
                except Exception as e:
                    results["errors"].append(f"Failed to run '{cmd}': {e}")

        return results

    def _filter_safe_commands(self, commands: str) -> list:
        """Filter commands to only allow safe ones"""
        safe_prefixes = [
            "npm ", "yarn ", "pnpm ",
            "pip ", "python ",
            "mkdir ", "touch ",
            "echo ", "cat ",
            "git init", "git add", "git commit",
            "npx ", "cargo ", "go "
        ]

        dangerous_patterns = [
            "rm -rf", "sudo", "chmod", "chown",
            "> /", "| sh", "| bash", "curl |", "wget |",
            "eval", "exec"
        ]

        safe = []
        for line in commands.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Check if dangerous
            is_dangerous = any(p in line for p in dangerous_patterns)
            if is_dangerous:
                continue

            # Check if safe
            is_safe = any(line.startswith(p) for p in safe_prefixes)
            if is_safe:
                safe.append(line)

        return safe

    def _get_allowed_tools(self, agent_id: str) -> list:
        """Get allowed tools based on agent type"""
        # Define tool permissions per agent role
        tool_sets = {
            "pm": ["Read", "Write", "Glob", "Grep"],
            "tech_lead": ["Read", "Write", "Glob", "Grep", "Bash"],
            "backend_dev": ["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
            "frontend_dev": ["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
            "fullstack_dev": ["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
            "qa_tester": ["Read", "Write", "Bash", "Glob", "Grep"],
            "devops": ["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
            "security_auditor": ["Read", "Glob", "Grep", "Bash"],
            "business_analyst": ["Read", "Write", "Glob", "Grep"],
            "uxui_designer": ["Read", "Write", "Glob", "Grep"]
        }

        return tool_sets.get(agent_id, ["Read", "Write", "Glob", "Grep"])


# CLI for testing
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run agent with LLM Router")
    parser.add_argument("agent", help="Agent ID (e.g., backend_dev)")
    parser.add_argument("--project", "-p", required=True, help="Project ID")
    parser.add_argument("--team", "-t", default="dev", help="Team ID")
    parser.add_argument("--provider", choices=["claude_code", "openrouter", "ollama"])
    parser.add_argument("--model", help="Model name")

    args = parser.parse_args()

    runner = AgentRunner(provider=args.provider, model=args.model)
    result = runner.run_with_tools(args.agent, args.team, args.project)

    print("\n" + "=" * 50)
    print(f"Agent: {args.agent}")
    print(f"Success: {result.get('success')}")
    if result.get("error"):
        print(f"Error: {result['error']}")
    if result.get("output"):
        print(f"Output: {result['output'][:500]}...")
