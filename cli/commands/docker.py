"""
Docker management commands
"""
import click
import subprocess


@click.group()
def docker():
    """Docker container management"""
    pass


@docker.command('list')
@click.pass_context
def list_containers(ctx):
    """List running containers"""
    config = ctx.obj

    if config.host != 'localhost':
        cmd = f"ssh {config.user}@{config.host} 'docker ps --format \"table {{{{.Names}}}}\\t{{{{.Status}}}}\\t{{{{.Ports}}}}\"'"
    else:
        cmd = 'docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"'

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            click.echo(result.stdout)
        else:
            click.echo("Failed to list containers")
            click.echo(result.stderr)
    except Exception as e:
        click.echo(f"Error: {e}")


@docker.command('logs')
@click.argument('container')
@click.option('--follow', '-f', is_flag=True, help='Follow log output')
@click.option('--tail', '-n', default=100, help='Number of lines')
@click.pass_context
def logs(ctx, container, follow, tail):
    """View container logs"""
    config = ctx.obj

    follow_flag = '-f' if follow else ''

    if config.host != 'localhost':
        cmd = f"ssh {config.user}@{config.host} 'docker logs {follow_flag} --tail {tail} {container}'"
    else:
        cmd = f'docker logs {follow_flag} --tail {tail} {container}'

    try:
        if follow:
            subprocess.run(cmd, shell=True)
        else:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            click.echo(result.stdout)
            if result.stderr:
                click.echo(result.stderr)
    except Exception as e:
        click.echo(f"Error: {e}")


@docker.command('restart')
@click.argument('container')
@click.pass_context
def restart(ctx, container):
    """Restart a container"""
    config = ctx.obj

    if config.host != 'localhost':
        cmd = f"ssh {config.user}@{config.host} 'docker restart {container}'"
    else:
        cmd = f'docker restart {container}'

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            click.echo(f"Restarted: {container}")
        else:
            click.echo(f"Failed to restart {container}")
            click.echo(result.stderr)
    except Exception as e:
        click.echo(f"Error: {e}")


@docker.command('stop')
@click.argument('container')
@click.pass_context
def stop(ctx, container):
    """Stop a container"""
    config = ctx.obj

    if config.host != 'localhost':
        cmd = f"ssh {config.user}@{config.host} 'docker stop {container}'"
    else:
        cmd = f'docker stop {container}'

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            click.echo(f"Stopped: {container}")
        else:
            click.echo(f"Failed to stop {container}")
            click.echo(result.stderr)
    except Exception as e:
        click.echo(f"Error: {e}")
