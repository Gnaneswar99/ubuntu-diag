"""Safe auto-remediation actions with dry-run support"""

import subprocess
from rich.console import Console
from rich.prompt import Confirm

console = Console()

class Remediator:
    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        self.actions_taken = []
    
    def execute(self, description, command, risk_level='low'):
        """Execute a remediation with safety checks"""
        console.print(f"\n[bold]Proposed fix:[/bold] {description}")
        console.print(f"[dim]Command: {' '.join(command)}[/dim]")
        console.print(f"[dim]Risk: {risk_level}[/dim]")
        
        if self.dry_run:
            console.print("[yellow]⏸  DRY RUN — skipping execution[/yellow]")
            self.actions_taken.append({
                'description': description,
                'command': ' '.join(command),
                'status': 'dry_run'
            })
            return True
        
        if risk_level == 'high':
            if not Confirm.ask("[red]HIGH RISK action. Proceed?[/red]"):
                self.actions_taken.append({
                    'description': description,
                    'command': ' '.join(command),
                    'status': 'skipped_by_user'
                })
                return False
        
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=30)
            success = result.returncode == 0
            self.actions_taken.append({
                'description': description,
                'command': ' '.join(command),
                'status': 'success' if success else 'failed',
                'output': result.stdout + result.stderr
            })
            if success:
                console.print("[green]✓ Fix applied successfully[/green]")
            else:
                console.print(f"[red]✗ Fix failed: {result.stderr}[/red]")
            return success
        except Exception as e:
            console.print(f"[red]✗ Error: {e}[/red]")
            self.actions_taken.append({
                'description': description,
                'command': ' '.join(command),
                'status': f'error: {e}'
            })
            return False

    def clean_journal_logs(self):
        return self.execute(
            "Vacuum journal logs older than 3 days",
            ['journalctl', '--vacuum-time=3d'],
            risk_level='low'
        )
    
    def restart_failed_service(self, service_name):
        return self.execute(
            f"Restart failed service: {service_name}",
            ['systemctl', 'restart', service_name],
            risk_level='medium'
        )
    
    def clean_apt_cache(self):
        return self.execute(
            "Clean apt package cache",
            ['apt-get', 'clean'],
            risk_level='low'
        )
    
    def fix_dns(self):
        return self.execute(
            "Restart systemd-resolved for DNS",
            ['systemctl', 'restart', 'systemd-resolved'],
            risk_level='medium'
        )
    
    def apt_autoremove(self):
        return self.execute(
            "Remove unused packages",
            ['apt-get', 'autoremove', '-y'],
            risk_level='low'
        )
