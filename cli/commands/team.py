"""
Team management commands
"""
import click
from pathlib import Path
import yaml


TEAMS_DIR = Path(__file__).parent.parent.parent / 'platform' / 'teams'


@click.group()
def team():
    """Team management commands"""
    pass


@team.command('list')
def list_teams():
    """List all teams"""
    if not TEAMS_DIR.exists():
        click.echo("No teams found.")
        return

    teams = []
    for team_dir in TEAMS_DIR.iterdir():
        if not team_dir.is_dir():
            continue

        # Count agents in team
        agents_dir = team_dir / 'agents'
        agent_count = len(list(agents_dir.glob('*.yaml'))) if agents_dir.exists() else 0

        # Load team config if exists
        config_file = team_dir / 'team.yaml'
        if config_file.exists():
            try:
                config = yaml.safe_load(config_file.read_text(encoding='utf-8'))
                teams.append({
                    'id': team_dir.name,
                    'name': config.get('name', team_dir.name),
                    'description': config.get('description', ''),
                    'agents': agent_count
                })
            except:
                teams.append({'id': team_dir.name, 'name': team_dir.name, 'agents': agent_count})
        else:
            teams.append({'id': team_dir.name, 'name': team_dir.name, 'agents': agent_count})

    if not teams:
        click.echo("No teams found.")
        return

    click.echo(f"{'Team':<15} {'Name':<20} {'Agents':<8} Description")
    click.echo("-" * 70)

    for t in teams:
        desc = t.get('description', '')[:30]
        click.echo(f"{t['id']:<15} {t['name']:<20} {t['agents']:<8} {desc}")


@team.command('show')
@click.argument('team_id')
def show_team(team_id):
    """Show team details and agents"""
    team_dir = TEAMS_DIR / team_id

    if not team_dir.exists():
        click.echo(f"Team not found: {team_id}", err=True)
        return

    click.echo(f"Team: {team_id}")

    # Load team config
    config_file = team_dir / 'team.yaml'
    if config_file.exists():
        try:
            config = yaml.safe_load(config_file.read_text(encoding='utf-8'))
            click.echo(f"Name: {config.get('name', team_id)}")
            click.echo(f"Description: {config.get('description', 'N/A')}")
        except:
            pass

    # List agents
    agents_dir = team_dir / 'agents'
    if agents_dir.exists():
        click.echo(f"\nAgents:")
        for agent_file in sorted(agents_dir.glob('*.yaml')):
            try:
                data = yaml.safe_load(agent_file.read_text(encoding='utf-8'))
                click.echo(f"  - {data.get('id')}: {data.get('role')}")
            except:
                pass
