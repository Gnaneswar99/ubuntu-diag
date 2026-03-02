"""LXD/LXC container diagnostics"""

import subprocess
import json

def check_all():
    findings = []
    findings.extend(check_lxd_running())
    findings.extend(check_container_health())
    return findings

def check_lxd_running():
    """Check if LXD daemon is running"""
    findings = []
    try:
        result = subprocess.run(
            ['systemctl', 'is-active', 'snap.lxd.daemon'],
            capture_output=True, text=True, timeout=5
        )
        if result.stdout.strip() != 'active':
            findings.append({
                'severity': 'CRITICAL',
                'category': 'Containers',
                'issue': 'LXD daemon is not running',
                'remediation': 'Start: `sudo snap start lxd`'
            })
        else:
            findings.append({
                'severity': 'OK',
                'category': 'Containers',
                'issue': 'LXD daemon is running',
                'remediation': 'N/A'
            })
    except Exception:
        pass
    return findings

def check_container_health():
    """Check status of all LXD containers"""
    findings = []
    try:
        result = subprocess.run(
            ['lxc', 'list', '--format=json'],
            capture_output=True, text=True, timeout=10
        )
        containers = json.loads(result.stdout)
        
        if not containers:
            findings.append({
                'severity': 'INFO',
                'category': 'Containers',
                'issue': 'No LXD containers found',
                'remediation': 'Launch one: `lxc launch ubuntu:22.04 test-node`'
            })
            return findings
        
        error_ct = [c['name'] for c in containers if c['status'] == 'Error']
        stopped = [c['name'] for c in containers if c['status'] == 'Stopped']
        running = [c for c in containers if c['status'] == 'Running']
        
        if error_ct:
            findings.append({
                'severity': 'CRITICAL',
                'category': 'Containers',
                'issue': f'Container(s) in error: {", ".join(error_ct)}',
                'remediation': 'Check: `lxc info <name> --show-log`'
            })
        if stopped:
            findings.append({
                'severity': 'INFO',
                'category': 'Containers',
                'issue': f'{len(stopped)} stopped container(s)',
                'remediation': 'Start if needed: `lxc start <name>`'
            })
        if running:
            # Check resource limits
            for c in running:
                name = c['name']
                config = c.get('config', {})
                if not config.get('limits.memory'):
                    findings.append({
                        'severity': 'WARNING',
                        'category': 'Containers',
                        'issue': f'Container {name} has no memory limit',
                        'remediation': f'Set: `lxc config set {name} limits.memory 2GB`'
                    })
            findings.append({
                'severity': 'OK',
                'category': 'Containers',
                'issue': f'{len(running)} container(s) running',
                'remediation': 'N/A'
            })
    except FileNotFoundError:
        findings.append({
            'severity': 'INFO',
            'category': 'Containers',
            'issue': 'LXD not installed',
            'remediation': 'Install: `sudo snap install lxd`'
        })
    except Exception as e:
        findings.append({
            'severity': 'INFO',
            'category': 'Containers',
            'issue': f'Could not query LXD: {e}',
            'remediation': 'Check: `lxc list`'
        })
    return findings
