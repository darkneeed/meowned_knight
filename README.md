# hostctl

`hostctl` is a local CLI utility for bootstrap and hardening of an Ubuntu 24.04 host.

The project manages a fixed set of host modules: firewall, SSH hardening, Fail2Ban, Docker, BBR, bootstrap packages, and traffic hardening for VPN-facing nodes.

## Requirements

- Linux host
- Ubuntu 24.04
- root privileges
- Python 3
- `uv` for environment bootstrap when using `run.sh`

`hostctl` checks the runtime before execution and exits if the host is not a local Ubuntu 24.04 machine or if it is not started as `root`.

## Quick Start

Run the wrapper script:

```bash
sudo ./run.sh
```

This script:

- checks `python3`
- installs `uv` if needed
- creates/syncs `.venv`
- starts `main.py`

Direct run is also possible:

```bash
python3 main.py
```

## Modes

If you run `hostctl` without service codes and action flags, it opens an interactive menu:

```bash
sudo ./run.sh
```

If you pass service codes and exactly one action, it runs in CLI mode:

```bash
sudo ./run.sh 1 2 --status
sudo ./run.sh --all --activate
sudo ./run.sh 4 --install --dry-run
```

## Available Modules

`hostctl` uses numeric service codes:

1. `Firewall`  
   Configures UFW, default ingress policy, SSH allowance, and Docker-aware forwarding rules.
2. `SSH Hardening`  
   Applies key-based SSH defaults, validates `sshd` config, and reloads the service safely.
3. `Fail2Ban`  
   Enables SSH protection and optionally adds an nginx jail when nginx is installed.
4. `Docker`  
   Installs Docker Engine and writes a baseline `/etc/docker/daemon.json`.
5. `BBR`  
   Applies sysctl settings for `fq` and `tcp_congestion_control=bbr`.
6. `Bootstrap`  
   Installs and verifies core packages such as `curl`, `ca-certificates`, `git`, and `ufw`.
7. `TrafficGuard`  
   Applies network hardening sysctls and writes reviewed VPN camouflage examples.

## Actions

Exactly one action must be selected in CLI mode:

- `--install` installs packages and baseline configuration
- `--uninstall` removes packages and managed files when supported
- `--activate` enables the module and applies active configuration
- `--deactivate` disables the module or removes its active configuration
- `--status` inspects current state without changes
- `--info` explains what the module manages and which files it uses

Apply the chosen action to all modules with:

```bash
sudo ./run.sh --all --status
```

## Dry Run

Use `--dry-run` to inspect the intended changes without modifying the system:

```bash
sudo ./run.sh 1 4 7 --activate --dry-run
```

In this mode, commands are logged but files are not written and destructive changes are not applied.

## Files and State

- `app.log` stores application logs in the project root
- `.state/` stores backup state used before rewriting managed files

Managed configuration is written directly to system paths such as:

- `/etc/ssh/sshd_config.d/99-hostctl-hardening.conf`
- `/etc/fail2ban/jail.d/hostctl.local`
- `/etc/docker/daemon.json`
- `/etc/sysctl.d/99-hostctl-bbr.conf`
- `/etc/sysctl.d/99-hostctl-trafficguard.conf`

Some modules also write reviewed example files, for example under `/etc/hostctl/examples/`.

## Development

Install dependencies:

```bash
uv sync
```

Run tests:

```bash
pytest -q
```

Show CLI help:

```bash
python3 main.py --help
```
