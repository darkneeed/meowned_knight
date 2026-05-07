from __future__ import annotations

from app.core.contracts import Operation
from app.services.firewall import FirewallService
from app.services.traffic_guard import TrafficGuardService
from tests.fakes import FakeRuntime, FakeSystem


def test_traffic_guard_dry_run_reports_change_without_writing() -> None:
    system = FakeSystem(dry_run=True)
    runtime = FakeRuntime(system, dry_run=True)
    result = TrafficGuardService().activate(runtime)
    assert result.operation is Operation.ACTIVATE
    assert result.success is True
    assert result.changed is True
    assert TrafficGuardService.config_path not in system.files
    assert TrafficGuardService.nginx_example_path not in system.files
    assert TrafficGuardService.notes_path not in system.files


def test_firewall_container_profile_adds_docker_routing_logic() -> None:
    system = FakeSystem(files={"/etc/docker": ""})
    runtime = FakeRuntime(system)
    result = FirewallService().activate(runtime)
    assert result.success is True
    assert result.details["profile"] == "container-host"
    assert ["ufw", "default", "deny", "routed"] in system.recorded_commands
    assert "/etc/ufw/after.rules" in system.files
