"""Kernel-level diagnostics — dmesg errors, tainted kernel, sysctl checks"""

import subprocess

def check_all():
    findings = []
    findings.extend(check_kernel_taint())
    findings.extend(check_dmesg_errors())
    findings.extend(check_kernel_params())
    findings.extend(check_oom_kills())
    return findings

def check_kernel_taint():
    """Check if the kernel is tainted"""
    findings = []
    try:
        with open('/proc/sys/kernel/tainted', 'r') as f:
            taint_value = int(f.read().strip())
        
        if taint_value != 0:
            taint_flags = {
                0: 'Proprietary module loaded',
                1: 'Module force loaded',
                2: 'SMP not certified',
                3: 'Module force unloaded',
                12: 'Working around hardware bug',
                13: 'Unsigned module loaded',
            }
            reasons = [desc for bit, desc in taint_flags.items()
                       if taint_value & (1 << bit)]
            
            findings.append({
                'severity': 'WARNING',
                'category': 'Kernel',
                'issue': f'Kernel tainted (value={taint_value}): {", ".join(reasons)}',
                'remediation': 'Review loaded modules with `lsmod`. Remove proprietary/unsigned modules if possible.'
            })
        else:
            findings.append({
                'severity': 'OK',
                'category': 'Kernel',
                'issue': 'Kernel is not tainted',
                'remediation': 'N/A'
            })
    except Exception as e:
        findings.append({
            'severity': 'INFO',
            'category': 'Kernel',
            'issue': f'Could not read taint status: {e}',
            'remediation': 'Check /proc/sys/kernel/tainted manually'
        })
    return findings

def check_dmesg_errors():
    """Parse dmesg for critical errors"""
    findings = []
    try:
        result = subprocess.run(
            ['dmesg', '--level=err,crit,alert,emerg'],
            capture_output=True, text=True, timeout=10
        )
        errors = [e for e in result.stdout.strip().split('\n') if e.strip()]
        
        if errors:
            hardware_errors = [e for e in errors if any(
                kw in e.lower() for kw in ['hardware', 'mce', 'ecc', 'pcie'])]
            io_errors = [e for e in errors if 'i/o error' in e.lower()]
            
            if hardware_errors:
                findings.append({
                    'severity': 'CRITICAL',
                    'category': 'Kernel',
                    'issue': f'{len(hardware_errors)} hardware error(s) in dmesg',
                    'remediation': 'Check `dmesg | grep -i hardware`. May indicate failing components.'
                })
            if io_errors:
                findings.append({
                    'severity': 'CRITICAL',
                    'category': 'Kernel',
                    'issue': f'{len(io_errors)} I/O error(s) detected',
                    'remediation': 'Run `smartctl -a /dev/sdX` to check disk health.'
                })
            if errors and not hardware_errors and not io_errors:
                findings.append({
                    'severity': 'WARNING',
                    'category': 'Kernel',
                    'issue': f'{len(errors)} kernel error(s) in dmesg',
                    'remediation': 'Review with `dmesg --level=err,crit`'
                })
        else:
            findings.append({
                'severity': 'OK',
                'category': 'Kernel',
                'issue': 'No critical kernel errors in dmesg',
                'remediation': 'N/A'
            })
    except Exception as e:
        findings.append({
            'severity': 'INFO',
            'category': 'Kernel',
            'issue': f'Could not read dmesg: {e}',
            'remediation': 'Run `dmesg` manually (may need sudo)'
        })
    return findings

def check_kernel_params():
    """Check important sysctl parameters"""
    findings = []
    recommended = {
        'vm.swappiness': (lambda v: int(v) <= 60, 'High swappiness can degrade performance'),
        'fs.file-max': (lambda v: int(v) >= 65536, 'Low file-max can cause too many open files error'),
        'kernel.panic': (lambda v: int(v) >= 0, 'kernel.panic=0 means no auto-reboot on panic'),
    }
    
    for param, (check_fn, desc) in recommended.items():
        try:
            result = subprocess.run(
                ['sysctl', '-n', param],
                capture_output=True, text=True, timeout=5
            )
            value = result.stdout.strip()
            if not check_fn(value):
                findings.append({
                    'severity': 'WARNING',
                    'category': 'Kernel',
                    'issue': f'{param}={value} — {desc}',
                    'remediation': f'Adjust with `sysctl -w {param}=<value>`'
                })
        except Exception:
            pass
    return findings

def check_oom_kills():
    """Check for recent OOM kills"""
    findings = []
    try:
        result = subprocess.run(
            ['dmesg'], capture_output=True, text=True, timeout=10
        )
        oom_lines = [l for l in result.stdout.split('\n')
                     if 'oom-kill' in l.lower() or 'out of memory' in l.lower()]
        if oom_lines:
            findings.append({
                'severity': 'CRITICAL',
                'category': 'Kernel',
                'issue': f'{len(oom_lines)} OOM kill event(s) detected',
                'remediation': 'Check memory: `free -h`, top consumers: `ps aux --sort=-%mem | head`'
            })
    except Exception:
        pass
    return findings
