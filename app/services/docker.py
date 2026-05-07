from __future__ import annotations

from app.core.contracts import ModuleResult, Operation
from app.core.renderers import render_docker_daemon_config
from app.services.base import BaseService


class DockerService(BaseService):
    code = 4
    name = "Docker"
    config_path = "/etc/docker/daemon.json"
    packages = ["docker.io", "docker-compose-v2"]

    def install(self, runtime) -> ModuleResult:
        self.apt_install(runtime, self.packages)
        changed = runtime.system.write_text(self.config_path, render_docker_daemon_config())
        runtime.system.run(["systemctl", "enable", "--now", "docker"], check=True)
        return ModuleResult(
            code=self.code,
            name=self.name,
            operation=Operation.INSTALL,
            success=True,
            changed=True or changed,
            message="Docker engine and compose plugin installed.",
        )

    def apply(self, runtime) -> ModuleResult:
        result = self.install(runtime)
        result.operation = Operation.APPLY
        result.message = "Docker baseline applied."
        return result

    def uninstall(self, runtime) -> ModuleResult:
        runtime.system.run(["systemctl", "disable", "--now", "docker"], check=False)
        changed = runtime.system.remove_file(self.config_path)
        self.apt_remove(runtime, self.packages, purge=True)
        return ModuleResult(
            code=self.code,
            name=self.name,
            operation=Operation.UNINSTALL,
            success=True,
            changed=True or changed,
            message="Docker packages removed.",
        )

    def activate(self, runtime) -> ModuleResult:
        changed = runtime.system.write_text(self.config_path, render_docker_daemon_config())
        runtime.system.run(["systemctl", "enable", "--now", "docker"], check=True)
        return ModuleResult(
            code=self.code,
            name=self.name,
            operation=Operation.ACTIVATE,
            success=True,
            changed=True or changed,
            message="Docker daemon activated with hostctl baseline config.",
        )

    def deactivate(self, runtime) -> ModuleResult:
        runtime.system.run(["systemctl", "disable", "--now", "docker"], check=True)
        return ModuleResult(
            code=self.code,
            name=self.name,
            operation=Operation.DEACTIVATE,
            success=True,
            changed=True,
            message="Docker daemon disabled.",
        )

    def status(self, runtime) -> ModuleResult:
        version = runtime.system.run(["docker", "--version"])
        return ModuleResult(
            code=self.code,
            name=self.name,
            operation=Operation.STATUS,
            success=self.service_is_active(runtime, "docker"),
            message="Docker status inspected.",
            details={
                "enabled": "yes" if self.service_is_enabled(runtime, "docker") else "no",
                "active": "yes" if self.service_is_active(runtime, "docker") else "no",
                "version": version.stdout.strip() or "unavailable",
                "config_present": "yes" if runtime.system.file_exists(self.config_path) else "no",
            },
        )

    def info(self, runtime) -> ModuleResult:
        return ModuleResult(
            code=self.code,
            name=self.name,
            operation=Operation.INFO,
            success=True,
            message="Docker manages Ubuntu packages, daemon.json hardening and service lifecycle.",
            details={"config_path": self.config_path},
        )
