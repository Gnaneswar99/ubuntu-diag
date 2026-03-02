#!/usr/bin/env python3
"""ubuntu-diag: Ubuntu Infrastructure Diagnostics & Auto-Remediation Tool"""

import click
import subprocess
from rich.console import Console
from rich.table import Table
from diag import kernel, systemd, network, storage, containers, memory

console = Console()

@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Ubuntu Infrastructure Diagnostics & Auto-Remediation Tool"""
    pass

@cli.command()
@click.option('--full', is_flag=True, help='Run all diagnostic checks')
@click.option('--category', type=click.Choice(
    ['kernel', 'systemd', 'network', 'storage', 'containers', 'memory']),
    help='Run specific category')
def scan(full, category):
    """Scan system for infrastructure issues"""
    console.print("[bold blue]🔍 Ubuntu Infrastructure Diagnostic Scan[/bold blue]\n")
    
    findings = []
    
    if full or category == 'kernel' or category is None:
        findings.extend(kernel.check_all())
    if full or category == 'systemd' or category is None:
        findings.extend(systemd.check_all())
    if full or category == 'network' or category is None:
        findings.extend(network.check_all())
    if full or category == 'storage' or category is None:
        findings.extend(storage.check_all())
    if full or category == 'containers':
        findings.extend(containers.check_all())
    if full or category == 'memory':
        findings.extend(memory.check_all())
    
    display_findings(findings)
    return findings

@cli.command()
@click.option('--dry-run/--apply', default=True, help='Dry run (default) or apply fixes')
def fix(dry_run):
    """Auto-remediate detected issues"""
    from remediate.actions import Remediator
    
    mode = "DRY RUN" if dry_run else "LIVE"
    console.print(f"[bold blue]🔧 Auto-Remediation ({mode})[/bold blue]\n")
    
    # Step 1: Run diagnostics
    console.print("[bold]Step 1: Scanning for issues...[/bold]\n")
    findings = []
    findings.extend(kernel.check_all())
    findings.extend(systemd.check_all())
    findings.extend(network.check_all())
    findings.extend(storage.check_all())
    findings.extend(memory.check_all())
    
    # Filter only issues (not OK)
    issues = [f for f in findings if f['severity'] in ('CRITICAL', 'WARNING')]
    
    if not issues:
        console.print("[green]✓ No issues found! System is healthy.[/green]")
        return
    
    console.print(f"[yellow]Found {len(issues)} issue(s). Proposing fixes...[/yellow]\n")
    
    # Step 2: Propose and apply remediations
    remediate = Remediator(dry_run=dry_run)
    
    for finding in issues:
        issue_lower = finding['issue'].lower()
        
        if 'failed unit' in issue_lower:
            # Extract service names
            parts = finding['issue'].split(': ', 1)
            if len(parts) > 1:
                services = parts[1].split(', ')
                for svc in services:
                    remediate.restart_failed_service(svc.strip())
        
        elif 'dns' in issue_lower and 'failed' in issue_lower:
            remediate.fix_dns()
        
        elif '% full' in issue_lower and finding['severity'] == 'CRITICAL':
            remediate.clean_journal_logs()
            remediate.clean_apt_cache()
            remediate.apt_autoremove()
        
        elif 'kernel error' in issue_lower:
            console.print(f"\n[bold]Issue:[/bold] {finding['issue']}")
            console.print("[dim]Manual review needed: `sudo dmesg --level=err,crit`[/dim]")
        
        elif 'kernel.panic' in issue_lower:
            console.print(f"\n[bold]Issue:[/bold] {finding['issue']}")
            console.print("[dim]To auto-reboot on panic: `sudo sysctl -w kernel.panic=10`[/dim]")
        
        elif 'interface' in issue_lower and 'down' in issue_lower:
            import re
            match = re.search(r'Interface (\S+) is DOWN', finding['issue'])
            if match:
                iface = match.group(1)
                remediate.execute(
                    f"Bring up network interface {iface}",
                    ['ip', 'link', 'set', iface, 'up'],
                    risk_level='medium'
                )
    
    # Step 3: Summary
    console.print(f"\n[bold blue]Summary: {len(remediate.actions_taken)} action(s) proposed[/bold blue]")
    
    summary_table = Table(title="Remediation Summary")
    summary_table.add_column("Action", width=40)
    summary_table.add_column("Status", width=15)
    summary_table.add_column("Command", width=35)
    
    for action in remediate.actions_taken:
        status_color = {
            'dry_run': 'yellow', 'success': 'green',
            'failed': 'red', 'skipped_by_user': 'dim'
        }.get(action['status'], 'white')
        
        summary_table.add_row(
            action['description'],
            f"[{status_color}]{action['status']}[/{status_color}]",
            action['command']
        )
    
    console.print(summary_table)

@cli.command()
@click.argument('scenario', type=click.Choice([
    'disk-full', 'oom', 'network-down', 'service-crash'
]))
def simulate(scenario):
    """Deploy an LXD container that simulates a common issue"""
    console.print(f"[bold yellow]🧪 Simulating: {scenario}[/bold yellow]\n")
    
    container_name = f"diag-lab-{scenario}"
    
    # Check if container already exists
    result = subprocess.run(['lxc', 'info', container_name],
                          capture_output=True, text=True)
    if result.returncode == 0:
        console.print(f"[yellow]Container {container_name} already exists. Deleting...[/yellow]")
        subprocess.run(['lxc', 'delete', container_name, '--force'])
    
    # Launch container
    console.print(f"[blue]Launching Ubuntu 22.04 container: {container_name}...[/blue]")
    result = subprocess.run(['lxc', 'launch', 'ubuntu:22.04', container_name],
                          capture_output=True, text=True)
    if result.returncode != 0:
        console.print(f"[red]Failed to launch container: {result.stderr}[/red]")
        return
    console.print(f"[green]✓ Container {container_name} launched[/green]\n")
    
    # Wait for container to be ready
    import time
    console.print("[dim]Waiting for container to initialize...[/dim]")
    time.sleep(5)
    
    if scenario == 'disk-full':
        console.print("[yellow]→ Filling disk to simulate storage pressure...[/yellow]")
        subprocess.run([
            'lxc', 'exec', container_name, '--',
            'bash', '-c', 'dd if=/dev/zero of=/tmp/fill bs=1M count=500 2>/dev/null'
        ])
        subprocess.run([
            'lxc', 'exec', container_name, '--',
            'bash', '-c', 'dd if=/dev/zero of=/var/log/fake.log bs=1M count=200 2>/dev/null'
        ])
        console.print("[green]✓ 700MB of junk files created[/green]")
    
    elif scenario == 'oom':
        console.print("[yellow]→ Setting memory limit to 128MB...[/yellow]")
        subprocess.run(['lxc', 'config', 'set', container_name, 'limits.memory', '128MB'])
        subprocess.run(['lxc', 'restart', container_name])
        time.sleep(3)
        console.print("[green]✓ Container restarted with 128MB memory limit[/green]")
    
    elif scenario == 'network-down':
        console.print("[yellow]→ Breaking network inside container...[/yellow]")
        subprocess.run([
            'lxc', 'exec', container_name, '--',
            'bash', '-c', 'ip link set eth0 down 2>/dev/null; rm /etc/resolv.conf 2>/dev/null; echo "nameserver 192.0.2.1" > /etc/resolv.conf'
        ])
        console.print("[green]✓ Network interface down + DNS broken[/green]")
    
    elif scenario == 'service-crash':
        console.print("[yellow]→ Stopping critical services...[/yellow]")
        subprocess.run([
            'lxc', 'exec', container_name, '--',
            'bash', '-c', 'systemctl stop cron 2>/dev/null; systemctl stop ssh 2>/dev/null; systemctl mask cron 2>/dev/null'
        ])
        console.print("[green]✓ Services cron and ssh stopped, cron masked[/green]")
    
    # Instructions
    console.print(f"\n[bold]{'='*55}[/bold]")
    console.print(f"[bold green]Lab ready! Now troubleshoot it:[/bold green]\n")
    console.print(f"  1. Enter the container:")
    console.print(f"     [cyan]lxc exec {container_name} -- bash[/cyan]\n")
    console.print(f"  2. Diagnose from inside:")
    console.print(f"     [cyan]df -h[/cyan]              (check disk)")
    console.print(f"     [cyan]free -h[/cyan]             (check memory)")
    console.print(f"     [cyan]systemctl --failed[/cyan]  (check services)")
    console.print(f"     [cyan]ip addr show[/cyan]        (check network)")
    console.print(f"     [cyan]ping ubuntu.com[/cyan]     (test connectivity)\n")
    console.print(f"  3. Fix the issue and verify!\n")
    console.print(f"  4. Cleanup when done:")
    console.print(f"     [cyan]lxc delete {container_name} --force[/cyan]")
    console.print(f"[bold]{'='*55}[/bold]")

@cli.command()
def report():
    """Generate an incident diagnostic report"""
    from reports.generator import generate_report
    
    console.print("[bold blue]📋 Generating Incident Report...[/bold blue]\n")
    
    # Run all diagnostics
    findings = []
    findings.extend(kernel.check_all())
    findings.extend(systemd.check_all())
    findings.extend(network.check_all())
    findings.extend(storage.check_all())
    findings.extend(containers.check_all())
    findings.extend(memory.check_all())
    
    report_text = generate_report(findings)
    
    # Save report
    from datetime import datetime
    filename = f"incident_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(filename, 'w') as f:
        f.write(report_text)
    
    console.print(f"[green]✓ Report saved: {filename}[/green]")
    console.print(f"[dim]View with: cat {filename}[/dim]")

def display_findings(findings):
    """Display findings in a rich table"""
    table = Table(title="Diagnostic Results")
    table.add_column("Severity", style="bold", width=10)
    table.add_column("Category", width=12)
    table.add_column("Issue", width=40)
    table.add_column("Remediation", width=35)
    
    severity_colors = {
        'CRITICAL': 'red', 'WARNING': 'yellow',
        'INFO': 'blue', 'OK': 'green'
    }
    
    for f in findings:
        color = severity_colors.get(f['severity'], 'white')
        table.add_row(
            f"[{color}]{f['severity']}[/{color}]",
            f['category'],
            f['issue'],
            f.get('remediation', 'N/A')
        )
    
    console.print(table)

if __name__ == '__main__':
    cli()
