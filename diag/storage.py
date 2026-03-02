"""Storage diagnostics — disk space, inodes, mount issues"""

import subprocess

def check_all():
    findings = []
    findings.extend(check_disk_usage())
    findings.extend(check_inode_usage())
    findings.extend(check_readonly_mounts())
    return findings

def check_disk_usage():
    """Check filesystems running low on space"""
    findings = []
    try:
        result = subprocess.run(
            ['df', '-h', '--output=target,pcent,avail,fstype', '-x', 'tmpfs',
             '-x', 'devtmpfs', '-x', 'squashfs'],
            capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.strip().split('\n')[1:]:
            parts = line.split()
            if len(parts) >= 4:
                mount = parts[0]
                usage_pct = int(parts[1].replace('%', ''))
                avail = parts[2]
                fstype = parts[3]
                
                # Skip snap mounts (read-only squashfs, always 100%)
                if '/snap/' in mount:
                    continue
                
                # Skip WSL internal mounts
                if any(skip in mount for skip in ['/wsl/', '/init', '/modules/']):
                    continue
                
                if usage_pct >= 95:
                    findings.append({
                        'severity': 'CRITICAL',
                        'category': 'Storage',
                        'issue': f'{mount} is {usage_pct}% full ({avail} remaining)',
                        'remediation': f'Free space: `du -sh {mount}/* | sort -rh | head`'
                    })
                elif usage_pct >= 85:
                    findings.append({
                        'severity': 'WARNING',
                        'category': 'Storage',
                        'issue': f'{mount} is {usage_pct}% full ({avail} remaining)',
                        'remediation': 'Clean old packages: `sudo apt autoremove`'
                    })
                else:
                    findings.append({
                        'severity': 'OK',
                        'category': 'Storage',
                        'issue': f'{mount} usage OK ({usage_pct}%, {avail} free)',
                        'remediation': 'N/A'
                    })
    except Exception as e:
        findings.append({
            'severity': 'INFO',
            'category': 'Storage',
            'issue': f'Could not check disk usage: {e}',
            'remediation': 'Run `df -h` manually'
        })
    return findings

def check_inode_usage():
    """Check inode usage"""
    findings = []
    try:
        result = subprocess.run(
            ['df', '-i', '--output=target,ipcent', '-x', 'tmpfs',
             '-x', 'devtmpfs', '-x', 'squashfs'],
            capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.strip().split('\n')[1:]:
            parts = line.split()
            if len(parts) >= 2 and parts[1] != '-':
                mount = parts[0]
                if '/snap/' in mount:
                    continue
                inode_pct = int(parts[1].replace('%', ''))
                if inode_pct >= 90:
                    findings.append({
                        'severity': 'CRITICAL',
                        'category': 'Storage',
                        'issue': f'{mount} inode usage at {inode_pct}%',
                        'remediation': 'Find small files: `find / -xdev -printf "%h\\n" | sort | uniq -c | sort -rn | head`'
                    })
    except Exception:
        pass
    return findings

def check_readonly_mounts():
    """Detect filesystems mounted read-only"""
    findings = []
    try:
        # Detect if running in WSL
        is_wsl = False
        try:
            with open('/proc/version', 'r') as f:
                if 'microsoft' in f.read().lower():
                    is_wsl = True
        except Exception:
            pass
        
        with open('/proc/mounts', 'r') as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 4:
                    mount, options = parts[1], parts[3]
                    if mount in ('/', '/home', '/var', '/tmp'):
                        if 'ro,' in options or options.startswith('ro'):
                            # In WSL, root is often read-only overlay — skip
                            if is_wsl and mount == '/':
                                continue
                            findings.append({
                                'severity': 'CRITICAL',
                                'category': 'Storage',
                                'issue': f'{mount} is mounted READ-ONLY',
                                'remediation': f'Check dmesg for I/O errors. Try `mount -o remount,rw {mount}`'
                            })
    except Exception:
        pass
    return findings
