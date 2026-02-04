"""
System status commands
"""
import click
import subprocess
import os


@click.group()
def system():
    """System status commands"""
    pass


@system.command('status')
@click.pass_context
def status(ctx):
    """Show system status (CPU, RAM, Disk)"""
    config = ctx.obj

    click.echo("=== Witmind System Status ===\n")

    # Check if running on server or remote
    if config.host != 'localhost' and os.environ.get('SSH_CONNECTION'):
        _show_local_status()
    else:
        _show_remote_status(config)


def _show_local_status():
    """Show status for local machine"""
    import platform

    click.echo(f"Platform: {platform.system()} {platform.release()}")

    # CPU
    try:
        import psutil
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        click.echo(f"CPU: {cpu_percent}% ({cpu_count} cores)")

        # Memory
        mem = psutil.virtual_memory()
        click.echo(f"RAM: {mem.percent}% ({mem.used // (1024**3)}/{mem.total // (1024**3)} GB)")

        # Disk
        disk = psutil.disk_usage('/')
        click.echo(f"Disk: {disk.percent}% ({disk.used // (1024**3)}/{disk.total // (1024**3)} GB)")
    except ImportError:
        click.echo("Install psutil for detailed stats: pip install psutil")


def _show_remote_status(config):
    """Show status for remote server via SSH"""
    try:
        cmd = f"ssh {config.user}@{config.host} 'uptime; free -h; df -h /'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            click.echo(result.stdout)
        else:
            click.echo(f"Failed to connect to {config.host}")
            click.echo(result.stderr)
    except subprocess.TimeoutExpired:
        click.echo(f"Connection to {config.host} timed out")
    except Exception as e:
        click.echo(f"Error: {e}")


@system.command('info')
def info():
    """Show Witmind installation info"""
    from pathlib import Path

    witmind_dir = Path(__file__).parent.parent.parent.parent
    data_dir = Path.home() / 'witmind-data'
    env_file = Path.home() / '.env'

    click.echo("=== Witmind Info ===\n")
    click.echo(f"Installation: {witmind_dir}")
    click.echo(f"Data directory: {data_dir} {'(exists)' if data_dir.exists() else '(not found)'}")
    click.echo(f"Config file: {env_file} {'(exists)' if env_file.exists() else '(not found)'}")

    # Check env variables
    click.echo("\n=== Environment ===")
    env_vars = ['ANTHROPIC_API_KEY', 'OPENROUTER_API_KEY', 'DO_API_TOKEN']
    for var in env_vars:
        value = os.environ.get(var)
        if value:
            masked = value[:8] + '...' + value[-4:] if len(value) > 16 else '***'
            click.echo(f"{var}: {masked}")
        else:
            click.echo(f"{var}: (not set)")
