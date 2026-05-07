from __future__ import annotations

from app.core.contracts import ModuleResult, Operation
from app.core.renderers import render_fail2ban_jail
from app.services.base import BaseService


class Fail2BanService(BaseService):
    code = 3
    name = "Fail2Ban"
    config_path = "/etc/fail2ban/jail.d/hostctl.local"

    def _nginx_installed(self, runtime) -> bool:
        return self.package_installed(runtime, "nginx")

    def install(self, runtime) -> ModuleResult:
        self.apt_install(runtime, ["fail2ban"])
        return ModuleResult(
            code=self.code,
            name=self.name,
            operation=Operation.INSTALL,
            success=True,
            changed=True,
            message="Fail2Ban installed.",
        )

    def uninstall(self, runtime) -> ModuleResult:
        changed = runtime.system.remove_file(self.config_path)
        self.apt_remove(runtime, ["fail2ban"], purge=True)
        return ModuleResult(
            code=self.code,
            name=self.name,
            operation=Operation.UNINSTALL,
            success=True,
            changed=True or changed,
            message="Fail2Ban removed.",
        )

    def activate(self, runtime) -> ModuleResult:
        changed = runtime.system.write_text(
            self.config_path,
            render_fail2ban_jail(enable_nginx=self._nginx_installed(runtime)),
        )
        runtime.system.run(["systemctl", "enable", "--now", "fail2ban"], check=True)
        return ModuleResult(
            code=self.code,
            name=self.name,
            operation=Operation.ACTIVATE,
            success=True,
            changed=True or changed,
            message="Fail2Ban activated with sshd jail and optional nginx jail.",
        )

    def deactivate(self, runtime) -> ModuleResult:
        runtime.system.run(["systemctl", "disable", "--now", "fail2ban"], check=True)
        return ModuleResult(
            code=self.code,
            name=self.name,
            operation=Operation.DEACTIVATE,
            success=True,
            changed=True,
            message="Fail2Ban disabled.",
        )

    def status(self, runtime) -> ModuleResult:
        client_status = runtime.system.run(["fail2ban-client", "status"])
        return ModuleResult(
            code=self.code,
            name=self.name,
            operation=Operation.STATUS,
            success=self.service_is_active(runtime, "fail2ban"),
            message="Fail2Ban status inspected.",
            details={
                "enabled": "yes" if self.service_is_enabled(runtime, "fail2ban") else "no",
                "active": "yes" if self.service_is_active(runtime, "fail2ban") else "no",
                "jails": client_status.stdout.strip() or "unknown",
            },
        )

    def info(self, runtime) -> ModuleResult:
        return ModuleResult(
            code=self.code,
            name=self.name,
            operation=Operation.INFO,
            success=True,
            message="Fail2Ban manages a dedicated jail.d drop-in for sshd and optionally nginx-http-auth.",
            details={"config_path": self.config_path},
        )

