"""Generate structured incident reports from diagnostic findings"""

import subprocess
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
import os

def generate_report(findings, actions=None):
    hostname = subprocess.getoutput('hostname')
    ubuntu_ver = subprocess.getoutput('lsb_release -ds 2>/dev/null || cat /etc/os-release | head -1')
    kernel_ver = subprocess.getoutput('uname -r')
    uptime = subprocess.getoutput('uptime -p')
    
    findings_by_cat = {}
    for f in findings:
        findings_by_cat.setdefault(f['category'], []).append(f)
    
    context = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'hostname': hostname,
        'ubuntu_version': ubuntu_ver,
        'kernel_version': kernel_ver,
        'uptime': uptime,
        'total_checks': len(findings),
        'categories': list(findings_by_cat.keys()),
        'critical_count': len([f for f in findings if f['severity'] == 'CRITICAL']),
        'warning_count': len([f for f in findings if f['severity'] == 'WARNING']),
        'info_count': len([f for f in findings if f['severity'] == 'INFO']),
        'findings_by_category': findings_by_cat,
        'actions': actions or [],
        'recommendations': generate_recommendations(findings),
    }
    
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template('incident.md.j2')
    return template.render(context)

def generate_recommendations(findings):
    recs = []
    severities = [f['severity'] for f in findings]
    categories = set(f['category'] for f in findings if f['severity'] != 'OK')
    
    if 'CRITICAL' in severities:
        recs.append("Address all CRITICAL findings immediately.")
    if 'Storage' in categories:
        recs.append("Set up disk usage monitoring with alerts at 80% and 90%.")
    if 'Kernel' in categories:
        recs.append("Review kernel logs and consider log forwarding with rsyslog.")
    if 'Network' in categories:
        recs.append("Verify network config is persistent via netplan.")
    if 'Containers' in categories:
        recs.append("Set resource limits on all LXD containers.")
    recs.append("Schedule regular scans: `ubuntu-diag scan --full`")
    return recs
