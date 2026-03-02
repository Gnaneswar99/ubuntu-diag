"""Memory diagnostics"""
import psutil

def check_all():
    findings = []
    mem = psutil.virtual_memory()
    
    if mem.percent >= 90:
        findings.append({
            'severity': 'CRITICAL',
            'category': 'Memory',
            'issue': f'Memory usage at {mem.percent}% ({mem.available // (1024**2)}MB free)',
            'remediation': 'Check top consumers: `ps aux --sort=-%mem | head -10`'
        })
    elif mem.percent >= 75:
        findings.append({
            'severity': 'WARNING',
            'category': 'Memory',
            'issue': f'Memory usage at {mem.percent}%',
            'remediation': 'Monitor with `free -h` and `vmstat 1`'
        })
    else:
        findings.append({
            'severity': 'OK',
            'category': 'Memory',
            'issue': f'Memory usage normal ({mem.percent}%)',
            'remediation': 'N/A'
        })
    
    swap = psutil.swap_memory()
    if swap.total > 0 and swap.percent >= 50:
        findings.append({
            'severity': 'WARNING',
            'category': 'Memory',
            'issue': f'Swap usage at {swap.percent}%',
            'remediation': 'High swap = memory pressure. Check OOM logs in dmesg.'
        })
    
    return findings
