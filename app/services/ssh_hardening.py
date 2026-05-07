from __future__ import annotations

import os

from app.core.contracts import ModuleResult, Operation
from app.core.renderers import render_sshd_hardening
from app.services.base import BaseService


class SSHHardeningService(BaseService):
    code = 2
    name = "SSH Hardening"
    config_path = "/etc/ssh/sshd_config.d/99-hostctl-hardening.conf"

    def preflight(self, runtime) -> tuple[bool, dict[str, str]]:
        current_user = os.environ.get("SUDO_USER") or os.environ.get("USER") or "root"
        is_ssh_session = bool(os.environ.get("SSH_CONNECTION") or os.environ.get("SSH_TTY"))
        candidate_paths = [f"/home/{current_user}/.ssh/authorized_keys", "/root/.ssh/authorized_keys"]
        has_authorized_key = False
        for path in candidate_paths:
            if not runtime.system.file_exists(path):
                continue
            if runtime.system.read_text(path).strip():
                has_authorized_key = True
                break
        details = {
            "current_user": current_user,
            "ssh_session": "yes" if is_ssh_session else "no",
            "authorized_key_present": "yes" if has_authorized_key else "no",
        }
        if is_ssh_session and not has_authorized_key:
            return False, details
        return True, details

    def install(self, runtime) -> ModuleResult:
        return self.activate(runtime)

    def uninstall(self, runtime) -> ModuleResult:
        return self.deactivate(runtime)

    def activate(self, runtime) -> ModuleResult:
        ok, details = self.preflight(runtime)
        if not ok:
            return ModuleResult(
                code=self.code,
                name=self.name,
                operation=Operation.ACTIVATE,
                success=False,
                message="SSH preflight failed: no authorized key found for a live SSH session.",
                details=details,
            )
        changed = runtime.system.write_text(self.config_path, render_sshd_hardening())
        runtime.system.run(["sshd", "-t"], check=True)
        runtime.system.run(["systemctl", "reload", "ssh"], check=True)
        return ModuleResult(
            code=self.code,
            name=self.name,
            operation=Operation.ACTIVATE,
            success=True,
            changed=changed,
            message="SSH hardening applied after successful preflight.",
            details=details,
        )

    def deactivate(self, runtime) -> ModuleResult:
        changed = runtime.system.remove_file(self.config_path)
        runtime.system.run(["sshd", "-t"], check=True)
        runtime.system.run(["systemctl", "reload", "ssh"], check=True)
        return ModuleResult(
            code=self.code,
            name=self.name,
            operation=Operation.DEACTIVATE,
            success=True,
            changed=changed,
            message="SSH hardening removed.",
        )

    def status(self, runtime) -> ModuleResult:
        ok, details = self.preflight(runtime)
        service_active = self.service_is_active(runtime, "ssh")
        return ModuleResult(
            code=self.code,
            name=self.name,
            operation=Operation.STATUS,
            success=ok,
            message="SSH hardening status inspected.",
            details={
                **details,
                "config_present": "yes" if runtime.system.file_exists(self.config_path) else "no",
                "ssh_active": "yes" if service_active else "no",
            },
        )

    def info(self, runtime) -> ModuleResult:
        return ModuleResult(
            code=self.code,
            name=self.name,
            operation=Operation.INFO,
            success=True,
            message="SSH hardening writes a dedicated sshd drop-in with key-only defaults and validates syntax.",
            details={"config_path": self.config_path},
        )
