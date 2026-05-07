from __future__ import annotations

from app.services.ssh_hardening import SSHHardeningService
from tests.fakes import FakeRuntime, FakeSystem


def test_ssh_preflight_requires_authorized_key_for_live_session(monkeypatch) -> None:
    monkeypatch.setenv("SSH_CONNECTION", "10.0.0.1 22 10.0.0.2 12345")
    monkeypatch.setenv("SUDO_USER", "forge")
    runtime = FakeRuntime(FakeSystem())
    ok, details = SSHHardeningService().preflight(runtime)
    assert ok is False
    assert details["authorized_key_present"] == "no"


def test_ssh_preflight_passes_with_authorized_key(monkeypatch) -> None:
    monkeypatch.setenv("SSH_CONNECTION", "10.0.0.1 22 10.0.0.2 12345")
    monkeypatch.setenv("SUDO_USER", "forge")
    runtime = FakeRuntime(
        FakeSystem(files={"/home/forge/.ssh/authorized_keys": "ssh-ed25519 AAAATEST"}),
    )
    ok, details = SSHHardeningService().preflight(runtime)
    assert ok is True
    assert details["authorized_key_present"] == "yes"
