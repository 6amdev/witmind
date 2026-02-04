"""
Project management commands
"""
import click
import os
from datetime import datetime
from pathlib import Path


@click.group()
def project():
    """Project management commands"""
    pass


@project.command('new')
@click.argument('description')
@click.pass_context
def new(ctx, description):
    """Create a new project"""
    config = ctx.obj

    # Generate project ID
    timestamp = datetime.now().strftime('%Y%m%d')
    project_id = f"proj-{timestamp}-{os.urandom(3).hex()}"

    # Create project directory
    project_dir = config.projects_dir / project_id
    project_dir.mkdir(parents=True, exist_ok=True)

    # Create project.json
    import json
    project_data = {
        "id": project_id,
        "description": description,
        "created_at": datetime.now().isoformat(),
        "status": "created",
        "workflow": None,
        "agents_assigned": []
    }

    (project_dir / 'project.json').write_text(
        json.dumps(project_data, indent=2, ensure_ascii=False)
    )

    click.echo(f"Created project: {project_id}")
    click.echo(f"Location: {project_dir}")
    click.echo(f"\nNext steps:")
    click.echo(f"  wit run {project_id}")
    click.echo(f"  wit run {project_id} --auto-approve-all")


@project.command('list')
@click.pass_context
def list_projects(ctx):
    """List all projects"""
    config = ctx.obj

    if not config.projects_dir.exists():
        click.echo("No projects found.")
        return

    projects = sorted(config.projects_dir.iterdir(), reverse=True)

    if not projects:
        click.echo("No projects found.")
        return

    click.echo(f"{'ID':<25} {'Status':<12} {'Created':<20} Description")
    click.echo("-" * 80)

    import json
    for project_dir in projects:
        if not project_dir.is_dir():
            continue

        project_file = project_dir / 'project.json'
        if not project_file.exists():
            continue

        try:
            data = json.loads(project_file.read_text())
            created = data.get('created_at', '')[:16].replace('T', ' ')
            desc = data.get('description', '')[:30]
            status = data.get('status', 'unknown')
            click.echo(f"{data['id']:<25} {status:<12} {created:<20} {desc}")
        except:
            pass


@project.command('run')
@click.argument('project_id')
@click.option('--auto-approve-all', is_flag=True, help='Auto approve all steps')
@click.option('--preset', type=click.Choice(['max_quality', 'balanced', 'cost_saving', 'local_only']),
              default='balanced', help='LLM preset')
@click.option('--watch', is_flag=True, help='Watch logs after starting')
@click.pass_context
def run(ctx, project_id, auto_approve_all, preset, watch):
    """Run project workflow"""
    config = ctx.obj
    project_dir = config.projects_dir / project_id

    if not project_dir.exists():
        click.echo(f"Project not found: {project_id}", err=True)
        return

    click.echo(f"Starting workflow for {project_id}")
    click.echo(f"  Preset: {preset}")
    click.echo(f"  Auto-approve: {auto_approve_all}")

    # TODO: Integrate with Orchestrator
    click.echo("\n[Orchestrator integration pending]")
    click.echo("This will start the PM → Tech Lead → Dev → QA workflow")


@project.command('logs')
@click.argument('project_id')
@click.option('--follow', '-f', is_flag=True, help='Follow log output')
@click.pass_context
def logs(ctx, project_id, follow):
    """View project logs"""
    config = ctx.obj
    log_file = config.logs_dir / f"{project_id}.log"

    if not log_file.exists():
        click.echo(f"No logs found for: {project_id}")
        return

    if follow:
        import subprocess
        subprocess.run(['tail', '-f', str(log_file)])
    else:
        click.echo(log_file.read_text())
