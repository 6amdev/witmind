"""
Agent management commands
"""
import click
from pathlib import Path
import yaml


TEAMS_DIR = Path(__file__).parent.parent.parent / 'platform' / 'teams'


def load_agents():
    """Load all agents from YAML files"""
    agents = []

    if not TEAMS_DIR.exists():
        return agents

    for team_dir in TEAMS_DIR.iterdir():
        if not team_dir.is_dir():
            continue

        agents_dir = team_dir / 'agents'
        if not agents_dir.exists():
            continue

        for agent_file in agents_dir.glob('*.yaml'):
            try:
                data = yaml.safe_load(agent_file.read_text(encoding='utf-8'))
                data['team'] = team_dir.name
                agents.append(data)
            except:
                pass

    return agents


@click.group()
def agent():
    """Agent management commands"""
    pass


@agent.command('list')
@click.option('--team', '-t', help='Filter by team')
def list_agents(team):
    """List all available agents"""
    agents = load_agents()

    if team:
        agents = [a for a in agents if a.get('team') == team]

    if not agents:
        click.echo("No agents found.")
        return

    click.echo(f"{'Agent':<20} {'Team':<12} {'Role':<25} LLM")
    click.echo("-" * 70)

    for agent in sorted(agents, key=lambda x: (x.get('team', ''), x.get('id', ''))):
        agent_id = agent.get('id', 'unknown')
        team_name = agent.get('team', '')
        role = agent.get('role', '')[:25]
        llm = agent.get('llm', {}).get('model', 'default')
        click.echo(f"{agent_id:<20} {team_name:<12} {role:<25} {llm}")


@agent.command('run')
@click.argument('agent_id')
@click.option('--project', '-p', help='Project directory')
@click.option('--task', '-t', help='Task description')
@click.pass_context
def run_agent(ctx, agent_id, project, task):
    """Run a single agent"""
    agents = load_agents()
    agent_data = next((a for a in agents if a.get('id') == agent_id), None)

    if not agent_data:
        click.echo(f"Agent not found: {agent_id}", err=True)
        click.echo("Use 'wit agent list' to see available agents.")
        return

    click.echo(f"Running agent: {agent_id}")
    click.echo(f"  Team: {agent_data.get('team')}")
    click.echo(f"  Role: {agent_data.get('role')}")

    if project:
        click.echo(f"  Project: {project}")
    if task:
        click.echo(f"  Task: {task}")

    # TODO: Integrate with AgentRunner
    click.echo("\n[AgentRunner integration pending]")
    click.echo("This will run Claude Code with agent's tools and prompt")


@agent.command('show')
@click.argument('agent_id')
def show_agent(agent_id):
    """Show agent details"""
    agents = load_agents()
    agent_data = next((a for a in agents if a.get('id') == agent_id), None)

    if not agent_data:
        click.echo(f"Agent not found: {agent_id}", err=True)
        return

    click.echo(f"Agent: {agent_data.get('id')}")
    click.echo(f"Team: {agent_data.get('team')}")
    click.echo(f"Role: {agent_data.get('role')}")
    click.echo(f"Description: {agent_data.get('description', 'N/A')}")

    llm = agent_data.get('llm', {})
    click.echo(f"\nLLM Configuration:")
    click.echo(f"  Model: {llm.get('model', 'default')}")
    click.echo(f"  Provider: {llm.get('provider', 'anthropic')}")

    tools = agent_data.get('tools', [])
    if tools:
        click.echo(f"\nAllowed Tools: {', '.join(tools)}")
