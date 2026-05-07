from __future__ import annotations

from app.core.contracts import ModuleResult, Operation
from app.services.base import BaseService


class BootstrapService(BaseService):
    code = 6
    name = "Bootstrap"
    packages = ["curl", "ca-certificates", "git", "ufw"]

    def install(self, runtime) -> ModuleResult:
        self.apt_install(runtime, self.packages)
        result = self.status(runtime)
        result.operation = Operation.INSTALL
        result.success = True
        result.changed = True
        result.message = "Base packages updated and installed."
        return result

    def apply(self, runtime) -> ModuleResult:
        result = self.install(runtime)
        result.operation = Operation.APPLY
        result.message = "Bootstrap baseline applied."
        return result

    def uninstall(self, runtime) -> ModuleResult:
        return self.unsupported(Operation.UNINSTALL, "Bootstrap uninstall is not supported.")

    def activate(self, runtime) -> ModuleResult:
        return self.install(runtime)

    def deactivate(self, runtime) -> ModuleResult:
        return self.unsupported(Operation.DEACTIVATE, "Bootstrap deactivate is not supported.")

    def status(self, runtime) -> ModuleResult:
        package_status = {pkg: self.package_installed(runtime, pkg) for pkg in self.packages}
        hostname = runtime.system.run(["hostnamectl", "--static"]).stdout.strip()
        timedate = runtime.system.run(["timedatectl", "show", "--property=NTPSynchronized", "--value"]).stdout.strip()
        return ModuleResult(
            code=self.code,
            name=self.name,
            operation=Operation.STATUS,
            success=all(package_status.values()),
            message="Bootstrap prerequisites inspected.",
            details={
                "hostname": hostname or "unknown",
                "ntp_synchronized": timedate or "unknown",
                "packages": ", ".join(f"{name}={'yes' if state else 'no'}" for name, state in package_status.items()),
            },
        )

    def info(self, runtime) -> ModuleResult:
        result = self.status(runtime)
        result.operation = Operation.INFO
        result.message = "Bootstrap manages apt refresh, base packages, hostname and time checks."
        return result
