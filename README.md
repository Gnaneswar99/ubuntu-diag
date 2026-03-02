# ubuntu-diag 🔧

**Ubuntu Infrastructure Diagnostics & Auto-Remediation CLI Tool**

A Python-based CLI tool that performs full-stack diagnostics on Ubuntu systems — scanning the kernel, systemd services, networking, storage, LXD containers, and memory — then suggests and safely applies remediations. Includes an LXD-powered simulation lab for practicing real-world troubleshooting scenarios.

---

## Why This Project?

This tool was built to address a real gap in Ubuntu system administration: there's no single, lightweight tool that scans across **every layer of the infrastructure stack** and provides actionable remediation guidance in one place.

In enterprise support environments — like those at **Canonical** — engineers regularly troubleshoot complex, multi-layer issues where a kernel-level problem manifests as a storage failure, or a networking misconfiguration cascades into service crashes. This tool replicates that **cross-stack diagnostic workflow** in an automated, repeatable way.

### How It Aligns with Canonical's Software Support Engineer Role

| Role Requirement | How ubuntu-diag Demonstrates It |
|---|---|
| Resolve complex customer problems across Ubuntu, Kernel, Ceph, OpenStack, Kubernetes | Diagnoses real issues across kernel (dmesg, taint, OOM), systemd, networking, storage, and LXD containers |
| Work productively at any level of the stack including the kernel | Checks span from kernel parameters (`/proc/sys/`) and dmesg parsing all the way up to container orchestration via LXD |
| Develop bug fixes, backport patches, work with upstream | Remediation engine applies fixes programmatically; structured to be packageable as a snap for upstream distribution |
| Python, Go, C, C++ on Linux | Entire tool built in Python 3, interfacing directly with Linux subsystems via subprocess, `/proc`, `/sys`, and `psutil` |
| LXD/LXC containerization | First-class LXD integration: container health checks, resource limit auditing, and a simulation lab that launches real LXD containers with intentional faults |
| Troubleshooting and root-cause analysis | Every diagnostic module performs RCA and outputs specific, actionable fix commands |
| Clear technical communication | Generates structured incident reports with findings categorized by severity, plus prioritized recommendations |
| Participate in upstream communities | Open-source project structure with tests, packaging, and documentation ready for community contribution |

---

## Features

### 🔍 Full-Stack Diagnostics

- **Kernel** — Tainted kernel detection, dmesg error parsing (hardware failures, I/O errors), OOM kill detection, sysctl parameter validation
- **Systemd** — Failed unit detection, boot time analysis, critical service health verification (ssh, cron, journald, resolved)
- **Networking** — Interface status monitoring, IPv4 address validation, DNS resolution testing, default route verification, iptables firewall rule auditing
- **Storage** — Disk usage thresholds (warning at 85%, critical at 95%), inode exhaustion detection, read-only mount detection, snap/WSL-aware filtering to eliminate false positives
- **LXD Containers** — Daemon status, container health (running/stopped/error), resource limit auditing (memory, CPU)
- **Memory** — RAM usage monitoring, swap pressure detection

### 🔧 Auto-Remediation Engine

- **Dry-run by default** — See exactly what would be fixed before applying anything
- **Risk-level tagging** — Low, medium, and high risk classifications with interactive confirmation for dangerous operations
- **Smart matching** — Automatically maps detected issues to appropriate fixes (journal cleanup, service restart, DNS reset, apt cache cleaning)

### 🧪 LXD Simulation Lab

Spins up real Ubuntu 22.04 LXD containers with intentional problems for hands-on troubleshooting practice:

| Scenario | What It Breaks | Skills Practiced |
|---|---|---|
| `disk-full` | Fills 700MB of junk files in `/tmp` and `/var/log` | Storage diagnostics, log rotation, cleanup strategies |
| `oom` | Sets container memory limit to 128MB | Memory pressure analysis, OOM investigation, resource limits |
| `network-down` | Disables eth0, corrupts DNS config | Network troubleshooting, interface recovery, DNS debugging |
| `service-crash` | Stops and masks cron and ssh services | Systemd troubleshooting, service recovery, unit file analysis |

### 📋 Incident Report Generator

Produces structured Markdown reports containing system context (hostname, Ubuntu version, kernel, uptime), findings organized by category and severity, and prioritized remediation recommendations.

---

## Installation

### Prerequisites

- Ubuntu 18.04+ (tested on 22.04 LTS)
- Python 3.8+
- LXD (for container features): `sudo snap install lxd && sudo lxd init --auto`

### Setup

```bash
git clone https://github.com/Gnaneswar99/ubuntu-diag.git
cd ubuntu-diag
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

---

## Usage

### System Scan

```bash
# Full scan across all categories
sudo ubuntu-diag scan --full

# Scan a specific category
sudo ubuntu-diag scan --category kernel
sudo ubuntu-diag scan --category network
sudo ubuntu-diag scan --category storage
sudo ubuntu-diag scan --category systemd
sudo ubuntu-diag scan --category containers
sudo ubuntu-diag scan --category memory
```

**Example output:**

```
🔍 Ubuntu Infrastructure Diagnostic Scan

                         Diagnostic Results
┏━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Severity ┃ Category   ┃ Issue                      ┃ Remediation             ┃
┡━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ OK       │ Kernel     │ Kernel is not tainted      │ N/A                     │
│ WARNING  │ Kernel     │ 22 kernel error(s) in      │ Review with `dmesg      │
│          │            │ dmesg                      │ --level=err,crit`       │
│ OK       │ Systemd    │ No failed systemd units    │ N/A                     │
│ OK       │ Network    │ DNS resolution working     │ N/A                     │
│ OK       │ Storage    │ / usage OK (2%, 944G free) │ N/A                     │
│ WARNING  │ Containers │ Container test-node has    │ Set: `lxc config set    │
│          │            │ no memory limit            │ test-node limits.memory │
│          │            │                            │ 2GB`                    │
│ OK       │ Memory     │ Memory usage normal (12%)  │ N/A                     │
└──────────┴────────────┴────────────────────────────┴─────────────────────────┘
```

### Auto-Remediation

```bash
# Dry run — preview what would be fixed (safe, default)
sudo ubuntu-diag fix --dry-run

# Apply fixes for real
sudo ubuntu-diag fix --apply
```

### LXD Simulation Lab

```bash
# Launch a broken container to practice troubleshooting
ubuntu-diag simulate service-crash
ubuntu-diag simulate disk-full
ubuntu-diag simulate network-down
ubuntu-diag simulate oom

# Enter the container and diagnose
lxc exec diag-lab-service-crash -- bash

# Inside the container:
systemctl --failed       # Find broken services
journalctl -u cron       # Check logs
systemctl unmask cron    # Fix masked service
systemctl start cron     # Restart it

# Cleanup
lxc delete diag-lab-service-crash --force
```

### Incident Report

```bash
sudo ubuntu-diag report
cat incident_report_*.md
```

Generates a report like:

```markdown
# Incident Diagnostic Report
Generated: 2026-03-01 19:16:50
Hostname: server-prod-01
Ubuntu Version: Ubuntu 22.04.5 LTS
Kernel: 5.15.0-91-generic

## Executive Summary
Scanned 15 checks across 6 categories.
Found 0 critical, 4 warning, and 0 informational issues.

## Recommended Next Steps
1. Review kernel logs and consider log forwarding with rsyslog.
2. Set resource limits on all LXD containers.
3. Schedule regular scans: `ubuntu-diag scan --full`
```

---

## Project Architecture

```
ubuntu-diag/
├── cli.py                    # Main CLI — Click framework with 4 commands
│                             #   scan    → Run diagnostic checks
│                             #   fix     → Auto-remediate with dry-run
│                             #   simulate → LXD lab deployment
│                             #   report  → Incident report generation
├── diag/                     # Diagnostic modules (one per stack layer)
│   ├── kernel.py             # /proc/sys/kernel/tainted, dmesg, sysctl, OOM
│   ├── systemd.py            # systemctl, systemd-analyze, service health
│   ├── network.py            # ip addr, DNS resolution, routing, iptables
│   ├── storage.py            # df, inode usage, /proc/mounts, WSL-aware
│   ├── containers.py         # LXD daemon, container status, resource limits
│   └── memory.py             # psutil RAM/swap monitoring
├── remediate/
│   └── actions.py            # Remediator class with dry-run, risk levels
├── reports/
│   ├── generator.py          # Jinja2-based report renderer
│   └── templates/
│       └── incident.md.j2    # Markdown report template
├── tests/                    # Unit tests with mocked system calls
│   ├── test_kernel.py        # 8 tests: taint, dmesg, OOM
│   ├── test_network.py       # 4 tests: DNS, routing
│   └── test_storage.py       # 5 tests: disk, inodes, read-only
├── setup.py                  # pip installable package
├── .gitignore
└── README.md
```

---

## Design Decisions

**Why Python?** — Canonical's support tooling is heavily Python-based. Ubuntu ships with Python 3, and tools like `cloud-init`, `netplan`, and `ubuntu-advantage-tools` are all Python.

**Why LXD over Docker?** — LXD is Canonical's own system container manager. It provides full OS containers (not application containers), making it ideal for simulating real Ubuntu environments for diagnostics.

**Why subprocess over libraries?** — In support engineering, you need to understand the underlying CLI tools (dmesg, systemctl, ip, df). Using subprocess ensures the tool works the same way an engineer would manually, and the output parsing skills transfer directly to real troubleshooting.

**Why WSL-aware filtering?** — Real-world support tools must handle edge cases. Snap squashfs mounts always report 100% usage, and WSL overlays report read-only root — filtering these eliminates false positives that would erode trust in the tool.

---

## Testing

```bash
# Run all tests
python3 -m pytest tests/ -v

# Expected: 17 passed
tests/test_kernel.py::TestKernelTaint::test_clean_kernel PASSED
tests/test_kernel.py::TestKernelTaint::test_tainted_kernel PASSED
tests/test_kernel.py::TestKernelTaint::test_proprietary_module PASSED
tests/test_kernel.py::TestDmesgErrors::test_no_errors PASSED
tests/test_kernel.py::TestDmesgErrors::test_hardware_errors PASSED
tests/test_kernel.py::TestDmesgErrors::test_io_errors PASSED
tests/test_kernel.py::TestOOMKills::test_oom_detected PASSED
tests/test_kernel.py::TestOOMKills::test_no_oom PASSED
tests/test_network.py::TestDNS::test_dns_working PASSED
tests/test_network.py::TestDNS::test_dns_failure PASSED
tests/test_network.py::TestDefaultRoute::test_route_exists PASSED
tests/test_network.py::TestDefaultRoute::test_no_route PASSED
tests/test_storage.py::TestDiskUsage::test_healthy_disk PASSED
tests/test_storage.py::TestDiskUsage::test_critical_disk PASSED
tests/test_storage.py::TestDiskUsage::test_warning_disk PASSED
tests/test_storage.py::TestDiskUsage::test_snap_mounts_skipped PASSED
tests/test_storage.py::TestReadonlyMounts::test_readonly_root PASSED
```

Tests use `unittest.mock` to simulate system states (tainted kernels, disk failures, DNS outages) without requiring root access or modifying the actual system.

---

## Future Roadmap

- **Ceph diagnostics** — Cluster health via `ceph status`, OSD checks, PG analysis
- **OpenStack checks** — Nova, Neutron, Keystone service verification
- **Kubernetes integration** — Pod health, node status, resource quotas via `kubectl`
- **Juju integration** — Check Juju-deployed service health
- **MAAS integration** — Bare-metal provisioning status
- **Snap packaging** — Distribute as a snap via Snapcraft for easy installation across Ubuntu systems
- **Prometheus exporter** — Export diagnostic findings as metrics for monitoring dashboards

---

## Tech Stack

| Component | Technology | Why |
|---|---|---|
| Language | Python 3.10 | Ubuntu's default, Canonical's primary scripting language |
| CLI Framework | Click | Industry standard, used in many Canonical tools |
| Terminal UI | Rich | Colored tables for clear diagnostic output |
| Templating | Jinja2 | Used by Ansible, cloud-init — familiar in Canonical's ecosystem |
| System Metrics | psutil | Cross-platform system monitoring |
| Containers | LXD/LXC | Canonical's own container technology |
| Testing | pytest + unittest.mock | Mocked system calls for safe, repeatable tests |
| Packaging | setuptools | pip-installable, snap-ready |

---

## Author

**Gnaneswar M**
- GitHub: [github.com/Gnaneswar99](https://github.com/Gnaneswar99)
- LinkedIn: [linkedin.com/in/gnaneswarm](https://linkedin.com/in/gnaneswarm)
- Email: gnaneswarm2024@gmail.com

---

## License

MIT License — free to use, modify, and distribute.
