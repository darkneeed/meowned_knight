from __future__ import annotations

from app.core.contracts import ModuleResult, Operation
from app.core.renderers import render_ufw_docker_block
from app.services.base import BaseService


class FirewallService(BaseService):
    code = 1
    name = "Firewall"
    docker_rules_path = "/etc/ufw/after.rules"
    ufw_defaults_path = "/etc/default/ufw"

    def _profile(self, runtime) -> str:
        return "container-host" if runtime.system.file_exists("/etc/docker") else "base-host"

    def install(self, runtime) -> ModuleResult:
        self.apt_install(runtime, ["ufw"])
        return ModuleResult(
            code=self.code,
            name=self.name,
            operation=Operation.INSTALL,
            success=True,
            changed=True,
            message="UFW installed.",
        )

    def uninstall(self, runtime) -> ModuleResult:
        removed_block = runtime.system.remove_managed_block(self.docker_rules_path, "ufw-docker")
        self.apt_remove(runtime, ["ufw"], purge=True)
        return ModuleResult(
            code=self.code,
            name=self.name,
            operation=Operation.UNINSTALL,
            success=True,
            changed=True or removed_block,
            message="UFW removed.",
        )

    def activate(self, runtime) -> ModuleResult:
        changed = False
        profile = self._profile(runtime)
        runtime.system.run(["ufw", "default", "deny", "incoming"], check=True)
        runtime.system.run(["ufw", "default", "allow", "outgoing"], check=True)
        runtime.system.run(["ufw", "allow", "OpenSSH"], check=True)
        changed = True

        if profile == "container-host":
            runtime.system.run(["ufw", "default", "deny", "routed"], check=True)
            changed |= runtime.system.replace_or_append_line(
                self.ufw_defaults_path,
                r'^DEFAULT_FORWARD_POLICY=.*$',
                'DEFAULT_FORWARD_POLICY="DROP"',
            )
            changed |= runtime.system.ensure_managed_block(
                self.docker_rules_path,
                "ufw-docker",
                render_ufw_docker_block(),
            )

        runtime.system.run(["ufw", "--force", "enable"], check=True)
        return ModuleResult(
            code=self.code,
            name=self.name,
            operation=Operation.ACTIVATE,
            success=True,
            changed=changed,
            message=f"UFW profile {profile} activated.",
            details={"profile": profile},
        )

    def deactivate(self, runtime) -> ModuleResult:
        changed = runtime.system.remove_managed_block(self.docker_rules_path, "ufw-docker")
        runtime.system.run(["ufw", "--force", "disable"], check=True)
        return ModuleResult(
            code=self.code,
            name=self.name,
            operation=Operation.DEACTIVATE,
            success=True,
            changed=True or changed,
            message="UFW disabled.",
        )

    def status(self, runtime) -> ModuleResult:
        profile = self._profile(runtime)
        status_result = runtime.system.run(["ufw", "status", "verbose"])
        active = "Status: active" in status_result.stdout
        return ModuleResult(
            code=self.code,
            name=self.name,
            operation=Operation.STATUS,
            success=True,
            message="Firewall status inspected.",
            details={
                "profile": profile,
                "active": "yes" if active else "no",
                "docker_block": "present" if runtime.system.file_exists(self.docker_rules_path) else "absent",
            },
        )

    def info(self, runtime) -> ModuleResult:
        profile = self._profile(runtime)
        return ModuleResult(
            code=self.code,
            name=self.name,
            operation=Operation.INFO,
            success=True,
            message="Firewall manages UFW defaults, SSH allowance and Docker-aware routed policy.",
            details={
                "profile": profile,
                "defaults_file": self.ufw_defaults_path,
                "after_rules_file": self.docker_rules_path,
            },
        )

