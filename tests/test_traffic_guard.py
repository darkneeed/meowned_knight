from __future__ import annotations

from app.core.contracts import Operation
from app.services.traffic_guard import TrafficGuardService
from tests.fakes import FakeCommandResult, FakeRuntime, FakeSystem


def test_traffic_guard_activate_writes_vpn_examples() -> None:
    system = FakeSystem()
    runtime = FakeRuntime(system)

    result = TrafficGuardService().activate(runtime)

    assert result.operation is Operation.ACTIVATE
    assert result.success is True
    assert result.changed is True
    assert "ssl_reject_handshake on;" in system.files[TrafficGuardService.nginx_example_path]
    assert "silent drop or camouflage" in system.files[TrafficGuardService.notes_path]


def test_traffic_guard_status_reports_vpn_related_capabilities() -> None:
    commands = {
        ("sysctl", "-n", "net.ipv4.tcp_syncookies"): FakeCommandResult(
            command=["sysctl", "-n", "net.ipv4.tcp_syncookies"],
            stdout="1\n",
        ),
        ("sysctl", "-n", "net.ipv4.conf.all.rp_filter"): FakeCommandResult(
            command=["sysctl", "-n", "net.ipv4.conf.all.rp_filter"],
            stdout="1\n",
        ),
        ("sysctl", "-n", "net.ipv4.conf.all.accept_redirects"): FakeCommandResult(
            command=["sysctl", "-n", "net.ipv4.conf.all.accept_redirects"],
            stdout="0\n",
        ),
        ("dpkg-query", "-W", "-f=${Status}", "nginx"): FakeCommandResult(
            command=["dpkg-query", "-W", "-f=${Status}", "nginx"],
            stdout="install ok installed\n",
        ),
        ("dpkg-query", "-W", "-f=${Status}", "ipset"): FakeCommandResult(
            command=["dpkg-query", "-W", "-f=${Status}", "ipset"],
            stdout="install ok installed\n",
        ),
    }
    files = {
        TrafficGuardService.config_path: "configured",
        TrafficGuardService.nginx_example_path: "example",
        TrafficGuardService.notes_path: "notes",
    }
    runtime = FakeRuntime(FakeSystem(files=files, commands=commands))

    result = TrafficGuardService().status(runtime)

    assert result.operation is Operation.STATUS
    assert result.details["nginx_package"] == "yes"
    assert result.details["ipset_package"] == "yes"
    assert result.details["nginx_example"] == "present"
    assert result.details["vpn_notes"] == "present"


def test_traffic_guard_info_is_vpn_oriented() -> None:
    runtime = FakeRuntime(FakeSystem())

    result = TrafficGuardService().info(runtime)

    assert result.operation is Operation.INFO
    assert result.details["policy"] == "silent-drop-or-camouflage"
    assert result.details["rkn_strategy"] == "best-effort-ipset-bgp-feeds"
