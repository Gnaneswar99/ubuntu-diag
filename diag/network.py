"""Network diagnostics — interfaces, DNS, routes, firewall"""

import subprocess
import socket
import json

def check_all():
    findings = []
    findings.extend(check_interfaces())
    findings.extend(check_dns_resolution())
    findings.extend(check_default_route())
    findings.extend(check_firewall())
    return findings

def check_interfaces():
    """Check network interfaces for issues"""
    findings = []
    try:
        result = subprocess.run(
            ['ip', '-j', 'addr', 'show'],
            capture_output=True, text=True, timeout=10
        )
        interfaces = json.loads(result.stdout)
        
        for iface in interfaces:
            name = iface.get('ifname', 'unknown')
            state = iface.get('operstate', 'UNKNOWN')
            
            if name == 'lo':
                continue
            
            if state == 'DOWN':
                findings.append({
                    'severity': 'WARNING',
                    'category': 'Network',
                    'issue': f'Interface {name} is DOWN',
                    'remediation': f'Bring up: `ip link set {name} up` or check /etc/netplan/'
                })
            
            addr_info = iface.get('addr_info', [])
            ipv4 = [a for a in addr_info if a.get('family') == 'inet']
            if state == 'UP' and not ipv4:
                findings.append({
                    'severity': 'WARNING',
                    'category': 'Network',
                    'issue': f'Interface {name} is UP but has no IPv4 address',
                    'remediation': 'Check DHCP: `journalctl -u systemd-networkd`'
                })
    except Exception as e:
        findings.append({
            'severity': 'INFO',
            'category': 'Network',
            'issue': f'Could not check interfaces: {e}',
            'remediation': 'Run `ip addr show` manually'
        })
    return findings

def check_dns_resolution():
    """Verify DNS resolution is working"""
    findings = []
    test_domains = ['ubuntu.com', 'archive.ubuntu.com']
    
    for domain in test_domains:
        try:
            socket.getaddrinfo(domain, None, socket.AF_INET)
        except socket.gaierror:
            findings.append({
                'severity': 'CRITICAL',
                'category': 'Network',
                'issue': f'DNS resolution failed for {domain}',
                'remediation': 'Check /etc/resolv.conf and `resolvectl status`. Try `ping 8.8.8.8`'
            })
            return findings
    
    findings.append({
        'severity': 'OK',
        'category': 'Network',
        'issue': 'DNS resolution working',
        'remediation': 'N/A'
    })
    return findings

def check_default_route():
    """Check for default route"""
    findings = []
    try:
        result = subprocess.run(
            ['ip', 'route', 'show', 'default'],
            capture_output=True, text=True, timeout=5
        )
        if not result.stdout.strip():
            findings.append({
                'severity': 'CRITICAL',
                'category': 'Network',
                'issue': 'No default route configured',
                'remediation': 'Add: `ip route add default via <gateway>` or check netplan'
            })
        else:
            findings.append({
                'severity': 'OK',
                'category': 'Network',
                'issue': 'Default route configured',
                'remediation': 'N/A'
            })
    except Exception:
        pass
    return findings

def check_firewall():
    """Check iptables rules"""
    findings = []
    try:
        result = subprocess.run(
            ['iptables', '-L', '-n', '--line-numbers'],
            capture_output=True, text=True, timeout=5
        )
        drop_rules = [l for l in result.stdout.split('\n')
                      if 'DROP' in l or 'REJECT' in l]
        if drop_rules:
            findings.append({
                'severity': 'INFO',
                'category': 'Network',
                'issue': f'{len(drop_rules)} DROP/REJECT firewall rule(s) active',
                'remediation': 'Review: `iptables -L -n -v` — ensure needed ports are open'
            })
    except Exception:
        pass
    return findings
