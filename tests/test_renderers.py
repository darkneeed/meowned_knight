from __future__ import annotations

from app.core.renderers import (
    render_bbr_sysctl,
    render_docker_daemon_config,
    render_fail2ban_jail,
    render_sshd_hardening,
    render_traffic_guard_sysctl,
    render_ufw_docker_block,
    render_vpn_camouflage_nginx,
    render_vpn_hardening_notes,
)


def test_renderers_include_expected_content() -> None:
    assert "PasswordAuthentication no" in render_sshd_hardening()
    assert "[sshd]" in render_fail2ban_jail(enable_nginx=False)
    assert "[nginx-http-auth]" in render_fail2ban_jail(enable_nginx=True)
    assert '"icc": false' in render_docker_daemon_config()
    assert "tcp_congestion_control=bbr" in render_bbr_sysctl()
    assert "net.ipv4.tcp_syncookies=1" in render_traffic_guard_sysctl()
    assert ":DOCKER-USER - [0:0]" in render_ufw_docker_block()
    assert "ssl_reject_handshake on;" in render_vpn_camouflage_nginx()
    assert "return 444;" in render_vpn_camouflage_nginx()
    assert "silent drop or camouflage" in render_vpn_hardening_notes()
