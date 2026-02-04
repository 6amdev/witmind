#!/usr/bin/env python3
"""
Witmind CLI - Unified command line interface for AI Agent Platform

Usage:
    wit new "Project description"    # Create new project
    wit run proj-xxx                 # Run workflow
    wit agent list                   # List agents
    wit status                       # System status
    wit docker list                  # Docker containers
    wit do ddns 6amdev.com home      # Update DDNS
"""

import click
import os
import sys
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment from ~/.env
from dotenv import load_dotenv
env_file = Path.home() / '.env'
if env_file.exists():
    load_dotenv(env_file)

# Import command modules
from commands import project, agent, team, system, docker, cloud

__version__ = '2.0.0'


class Config:
    """Global configuration"""
    def __init__(self):
        self.host = os.environ.get('SERVER_HOST', 'localhost')
        self.user = os.environ.get('SERVER_USER', 'wit')
        self.ssh_key = os.environ.get('SERVER_SSH_KEY', '')
        self.verbose = False
        self.data_dir = Path.home() / 'witmind-data'
        self.projects_dir = self.data_dir / 'projects'
        self.logs_dir = self.data_dir / 'logs'


pass_config = click.make_pass_decorator(Config, ensure=True)


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.version_option(__version__, prog_name='wit')
@click.pass_context
def cli(ctx, verbose):
    """
    Witmind CLI - AI Agent Platform

    \b
    Project Management:
      wit new "Build Todo App"       Create new project
      wit list                       List all projects
      wit run proj-xxx               Run workflow
      wit logs proj-xxx              View logs

    \b
    Agent Commands:
      wit agent list                 List all agents
      wit agent run frontend_dev    Run single agent
      wit team list                  List teams

    \b
    Infrastructure:
      wit status                     System status
      wit docker list                Docker containers
      wit do ddns 6amdev.com home   Update DDNS

    \b
    Configuration:
      Create ~/.env from .env.example and fill in your values.
    """
    ctx.ensure_object(Config)
    ctx.obj.verbose = verbose


# Register command groups
cli.add_command(project.project)
cli.add_command(agent.agent)
cli.add_command(team.team)
cli.add_command(system.system)
cli.add_command(docker.docker)
cli.add_command(cloud.do, name='do')


# Quick shortcuts
@cli.command('new')
@click.argument('description')
@pass_config
def quick_new(config, description):
    """Create new project (shortcut for 'project new')"""
    ctx = click.get_current_context()
    ctx.invoke(project.new, description=description)


@cli.command('list')
@pass_config
def quick_list(config):
    """List projects (shortcut for 'project list')"""
    ctx = click.get_current_context()
    ctx.invoke(project.list_projects)


@cli.command('run')
@click.argument('project_id')
@click.option('--auto-approve-all', is_flag=True, help='Auto approve all steps')
@click.option('--preset', type=click.Choice(['max_quality', 'balanced', 'cost_saving', 'local_only']),
              default='balanced', help='LLM preset')
@click.option('--watch', is_flag=True, help='Watch logs after starting')
@pass_config
def quick_run(config, project_id, auto_approve_all, preset, watch):
    """Run project workflow (shortcut for 'project run')"""
    ctx = click.get_current_context()
    ctx.invoke(project.run, project_id=project_id,
               auto_approve_all=auto_approve_all, preset=preset, watch=watch)


@cli.command('logs')
@click.argument('project_id')
@click.option('--follow', '-f', is_flag=True, help='Follow log output')
@pass_config
def quick_logs(config, project_id, follow):
    """View project logs (shortcut for 'project logs')"""
    ctx = click.get_current_context()
    ctx.invoke(project.logs, project_id=project_id, follow=follow)


@cli.command('status')
@pass_config
def quick_status(config):
    """System status (shortcut for 'system status')"""
    ctx = click.get_current_context()
    ctx.invoke(system.status)


def main():
    cli()


if __name__ == '__main__':
    main()
