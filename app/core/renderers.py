from __future__ import annotations

import json


def render_sshd_hardening() -> str:
    lines = [
        "PasswordAuthentication no",
        "KbdInteractiveAuthentication no",
        "ChallengeResponseAuthentication no",
        "PermitRootLogin prohibit-password",
        "PubkeyAuthentication yes",
        "PermitEmptyPasswords no",
        "X11Forwarding no",
        "AllowAgentForwarding no",
        "AllowTcpForwarding no",
        "ClientAliveInterval 300",
        "ClientAliveCountMax 2",
        "LoginGraceTime 30",
        "MaxAuthTries 3",
        "MaxSessions 4",
        "UsePAM yes",
    ]
    return "\n".join(lines) + "\n"


def render_fail2ban_jail(enable_nginx: bool) -> str:
    sections = [
        "[DEFAULT]",
        "bantime = 1h",
        "findtime = 10m",
        "maxretry = 5",
        "backend = systemd",
        "",
        "[sshd]",
        "enabled = true",
        "port = ssh",
        "logpath = %(sshd_log)s",
    ]
    if enable_nginx:
        sections.extend(
            [
                "",
                "[nginx-http-auth]",
                "enabled = true",
            ]
        )
    return "\n".join(sections) + "\n"


def render_docker_daemon_config() -> str:
    payload = {
        "icc": False,
        "iptables": True,
        "live-restore": True,
        "log-driver": "json-file",
        "log-level": "warn",
        "log-opts": {"max-file": "3", "max-size": "10m"},
        "userland-proxy": False,
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def render_bbr_sysctl() -> str:
    return "\n".join(
        [
            "net.core.default_qdisc=fq",
            "net.ipv4.tcp_congestion_control=bbr",
            "",
        ]
    )


def render_traffic_guard_sysctl() -> str:
    return "\n".join(
        [
            "net.ipv4.tcp_syncookies=1",
            "net.ipv4.tcp_rfc1337=1",
            "net.ipv4.icmp_echo_ignore_broadcasts=1",
            "net.ipv4.icmp_ignore_bogus_error_responses=1",
            "net.ipv4.conf.all.rp_filter=1",
            "net.ipv4.conf.default.rp_filter=1",
            "net.ipv4.conf.all.accept_redirects=0",
            "net.ipv4.conf.default.accept_redirects=0",
            "net.ipv4.conf.all.secure_redirects=0",
            "net.ipv4.conf.default.secure_redirects=0",
            "net.ipv4.conf.all.send_redirects=0",
            "net.ipv4.conf.default.send_redirects=0",
            "net.ipv4.conf.all.accept_source_route=0",
            "net.ipv4.conf.default.accept_source_route=0",
            "net.ipv4.conf.all.log_martians=1",
            "net.ipv4.conf.default.log_martians=1",
            "net.ipv6.conf.all.accept_redirects=0",
            "net.ipv6.conf.default.accept_redirects=0",
            "net.ipv6.conf.all.accept_source_route=0",
            "net.ipv6.conf.default.accept_source_route=0",
            "",
        ]
    )


def render_vpn_camouflage_nginx() -> str:
    return "\n".join(
        [
            "# Example only: review before enabling on a public VPN-facing endpoint.",
            "map $http_user_agent $hostctl_suspicious_ua {",
            "    default 0;",
            '    "" 1;',
            "    ~*(curl|wget|python-requests|Go-http-client|libwww-perl|aiohttp) 1;",
            "}",
            "",
            "server {",
            "    listen 80 default_server;",
            "    listen [::]:80 default_server;",
            "    server_name _;",
            "    access_log off;",
            "",
            "    if ($hostctl_suspicious_ua) {",
            "        return 444;",
            "    }",
            "",
            "    return 444;",
            "}",
            "",
            "server {",
            "    listen 443 default_server ssl;",
            "    listen [::]:443 default_server ssl;",
            "    server_name _;",
            "",
            "    # Reject direct-IP and wrong-SNI probes without exposing a default certificate.",
            "    ssl_reject_handshake on;",
            "}",
            "",
        ]
    )


def render_vpn_hardening_notes() -> str:
    return "\n".join(
        [
            "VPN-facing response policy",
            "=========================",
            "",
            "1. Never return a VPN-specific response without a valid shared secret or key.",
            "2. Prefer silent drop or camouflage behind a generic web origin.",
            "3. Treat RKN/GRChC ipset or BGP-fed deny lists as best-effort because scanner IPs churn.",
            "4. Expect direct-IP probes without Host or usable SNI and handle them with a drop or TLS reject path.",
            "5. Drop empty or automation-heavy user agents such as curl, python-requests and Go-http-client,",
            "   while assuming advanced scanners can spoof Chrome-like headers.",
            "",
        ]
    )


def render_ufw_docker_block() -> str:
    return "\n".join(
        [
            "*filter",
            ":DOCKER-USER - [0:0]",
            "-A DOCKER-USER -m conntrack --ctstate RELATED,ESTABLISHED -j RETURN",
            "-A DOCKER-USER -j ufw-user-forward",
            "-A DOCKER-USER -j DROP",
            "COMMIT",
            "",
        ]
    )
