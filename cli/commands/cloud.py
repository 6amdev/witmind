"""
Cloud service commands (DigitalOcean)
"""
import click
import os
import json

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


DO_API_URL = "https://api.digitalocean.com/v2"


def get_token():
    """Get DigitalOcean API token from environment"""
    token = os.environ.get('DO_API_TOKEN')
    if not token:
        raise click.ClickException(
            "DO_API_TOKEN not set. Add it to ~/.env or export DO_API_TOKEN=xxx"
        )
    return token


def do_request(method, endpoint, data=None):
    """Make request to DigitalOcean API"""
    if not HAS_HTTPX:
        raise click.ClickException("httpx not installed. Run: pip install httpx")

    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    url = f"{DO_API_URL}/{endpoint}"

    if method == "GET":
        resp = httpx.get(url, headers=headers, timeout=30)
    elif method == "POST":
        resp = httpx.post(url, headers=headers, json=data, timeout=30)
    elif method == "PUT":
        resp = httpx.put(url, headers=headers, json=data, timeout=30)
    elif method == "DELETE":
        resp = httpx.delete(url, headers=headers, timeout=30)
    else:
        raise ValueError(f"Unknown method: {method}")

    if resp.status_code >= 400:
        raise click.ClickException(f"API Error: {resp.status_code} - {resp.text}")

    if resp.status_code == 204:
        return {}

    return resp.json()


@click.group(name='do')
def do():
    """DigitalOcean cloud commands"""
    pass


@do.command('account')
def account():
    """Show account info"""
    data = do_request("GET", "account")
    acc = data.get('account', {})

    click.echo(f"Email: {acc.get('email')}")
    click.echo(f"Status: {acc.get('status')}")
    click.echo(f"Droplet Limit: {acc.get('droplet_limit')}")


@do.command('balance')
def balance():
    """Show account balance"""
    data = do_request("GET", "customers/my/balance")

    click.echo(f"Month-to-date balance: ${data.get('month_to_date_balance', 0)}")
    click.echo(f"Account balance: ${data.get('account_balance', 0)}")


@do.command('dns')
@click.argument('action', type=click.Choice(['list', 'set', 'add', 'delete']))
@click.argument('domain')
@click.argument('args', nargs=-1)
def dns(action, domain, args):
    """Manage DNS records

    \b
    Examples:
      wit do dns list 6amdev.com
      wit do dns set 6amdev.com home 1.2.3.4
      wit do dns add 6amdev.com api 1.2.3.4
      wit do dns delete 6amdev.com 12345678
    """
    if action == 'list':
        data = do_request("GET", f"domains/{domain}/records")
        records = data.get('domain_records', [])

        click.echo(f"{'ID':<12} {'Type':<8} {'Name':<20} {'Data':<30} TTL")
        click.echo("-" * 80)

        for r in records:
            click.echo(f"{r['id']:<12} {r['type']:<8} {r['name']:<20} {r['data']:<30} {r['ttl']}")

    elif action == 'set':
        if len(args) < 2:
            raise click.ClickException("Usage: wit do dns set <domain> <subdomain> <ip>")

        subdomain, ip = args[0], args[1]

        # Get existing records
        data = do_request("GET", f"domains/{domain}/records")
        records = data.get('domain_records', [])

        existing = next((r for r in records if r['name'] == subdomain and r['type'] == 'A'), None)

        if existing:
            do_request("PUT", f"domains/{domain}/records/{existing['id']}", {"data": ip})
            click.echo(f"Updated: {subdomain}.{domain} -> {ip}")
        else:
            do_request("POST", f"domains/{domain}/records", {
                "type": "A",
                "name": subdomain,
                "data": ip,
                "ttl": 300
            })
            click.echo(f"Created: {subdomain}.{domain} -> {ip}")

    elif action == 'add':
        if len(args) < 2:
            raise click.ClickException("Usage: wit do dns add <domain> <subdomain> <ip>")

        subdomain, ip = args[0], args[1]
        do_request("POST", f"domains/{domain}/records", {
            "type": "A",
            "name": subdomain,
            "data": ip,
            "ttl": 300
        })
        click.echo(f"Created: {subdomain}.{domain} -> {ip}")

    elif action == 'delete':
        if len(args) < 1:
            raise click.ClickException("Usage: wit do dns delete <domain> <record_id>")

        record_id = args[0]
        do_request("DELETE", f"domains/{domain}/records/{record_id}")
        click.echo(f"Deleted record: {record_id}")


@do.command('ddns')
@click.argument('domain')
@click.argument('subdomain')
@click.option('--force', is_flag=True, help='Force update even if IP unchanged')
def ddns(domain, subdomain, force):
    """Update DDNS (Dynamic DNS)

    Detects current public IP and updates DNS record.

    Example:
      wit do ddns 6amdev.com home
    """
    # Get current public IP
    if not HAS_HTTPX:
        raise click.ClickException("httpx not installed. Run: pip install httpx")

    ip_services = [
        "https://api.ipify.org",
        "https://ifconfig.me/ip",
        "https://icanhazip.com",
    ]

    current_ip = None
    for service in ip_services:
        try:
            resp = httpx.get(service, timeout=10, follow_redirects=True)
            if resp.status_code == 200:
                ip = resp.text.strip()
                parts = ip.split('.')
                if len(parts) == 4 and all(p.isdigit() for p in parts):
                    current_ip = ip
                    break
        except:
            continue

    if not current_ip:
        raise click.ClickException("Could not detect public IP")

    click.echo(f"Current IP: {current_ip}")

    # Get existing record
    data = do_request("GET", f"domains/{domain}/records")
    records = data.get('domain_records', [])
    existing = next((r for r in records if r['name'] == subdomain and r['type'] == 'A'), None)

    if existing and existing['data'] == current_ip and not force:
        click.echo(f"DNS already up to date: {subdomain}.{domain} -> {current_ip}")
        return

    if existing:
        do_request("PUT", f"domains/{domain}/records/{existing['id']}", {"data": current_ip})
        click.echo(f"Updated: {subdomain}.{domain} -> {current_ip}")
    else:
        do_request("POST", f"domains/{domain}/records", {
            "type": "A",
            "name": subdomain,
            "data": current_ip,
            "ttl": 300
        })
        click.echo(f"Created: {subdomain}.{domain} -> {current_ip}")


@do.command('droplets')
def droplets():
    """List all droplets (VPS)"""
    data = do_request("GET", "droplets")
    droplets = data.get('droplets', [])

    if not droplets:
        click.echo("No droplets found.")
        return

    click.echo(f"{'ID':<12} {'Name':<20} {'Status':<10} {'IP':<16} Region")
    click.echo("-" * 70)

    for d in droplets:
        ip = d.get('networks', {}).get('v4', [{}])[0].get('ip_address', 'N/A')
        region = d.get('region', {}).get('slug', 'N/A')
        click.echo(f"{d['id']:<12} {d['name']:<20} {d['status']:<10} {ip:<16} {region}")
