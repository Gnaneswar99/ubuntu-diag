"""Systemd service health — failed units, slow boots, critical services"""

import subprocess
import re

def check_all():
    findings = []
    findings.extend(check_failed_units())
    findings.extend(check_boot_time())
    findings.extend(check_critical_services())
    return findings

def check_failed_units():
    """Identify failed systemd units"""
    findings = []
    try:
        result = subprocess.run(
            ['systemctl', 'list-units', '--state=failed', '--no-legend', '--no-pager', '--plain'],
            capture_output=True, text=True, timeout=10
        )
        failed = [l.strip() for l in result.stdout.strip().split('\n') if l.strip()]
        
        if failed:
            unit_names = [l.split()[0] for l in failed if l.split()]
            findings.append({
                'severity': 'CRITICAL',
                'category': 'Systemd',
                'issue': f'{len(unit_names)} failed unit(s): {", ".join(unit_names[:5])}',
                'remediation': 'Check logs: `journalctl -u <unit> -n 50`. Restart: `systemctl restart <unit>`'
            })
        else:
            findings.append({
                'severity': 'OK',
                'category': 'Systemd',
                'issue': 'No failed systemd units',
                'remediation': 'N/A'
            })
    except Exception as e:
        findings.append({
            'severity': 'INFO',
            'category': 'Systemd',
            'issue': f'Could not check systemd units: {e}',
            'remediation': 'Run `systemctl --failed` manually'
        })
    return findings

def check_boot_time():
    """Check if boot time is abnormally long"""
    findings = []
    try:
        result = subprocess.run(
            ['systemd-analyze'], capture_output=True, text=True, timeout=10
        )
        output = result.stdout.strip()
        match = re.search(r'= (.+)$', output.split('\n')[0])
        if match:
            time_str = match.group(1).strip()
            # Parse seconds
            sec_match = re.search(r'(\d+\.\d+)s', time_str)
            min_match = re.search(r'(\d+)min', time_str)
            total_sec = 0
            if min_match:
                total_sec += int(min_match.group(1)) * 60
            if sec_match:
                total_sec += float(sec_match.group(1))
            
            if total_sec > 120:
                findings.append({
                    'severity': 'WARNING',
                    'category': 'Systemd',
                    'issue': f'Slow boot time: {time_str}',
                    'remediation': 'Run `systemd-analyze blame` to find slow units.'
                })
            else:
                findings.append({
                    'severity': 'OK',
                    'category': 'Systemd',
                    'issue': f'Boot time normal: {time_str}',
                    'remediation': 'N/A'
                })
    except Exception:
        pass
    return findings

def check_critical_services():
    """Verify critical infrastructure services are running"""
    critical = ['ssh', 'systemd-resolved', 'systemd-journald', 'cron']
    findings = []
    
    for svc in critical:
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', svc],
                capture_output=True, text=True, timeout=5
            )
            if result.stdout.strip() != 'active':
                findings.append({
                    'severity': 'WARNING',
                    'category': 'Systemd',
                    'issue': f'Service {svc} is not active ({result.stdout.strip()})',
                    'remediation': f'Start: `systemctl start {svc}` Check: `journalctl -u {svc}`'
                })
        except Exception:
            pass
    return findings
