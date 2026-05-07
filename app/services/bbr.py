from __future__ import annotations

from app.core.contracts import ModuleResult, Operation
from app.core.renderers import render_bbr_sysctl
from app.services.base import BaseService


class BBRService(BaseService):
    code = 5
    name = "BBR"
    config_path = "/etc/sysctl.d/99-hostctl-bbr.conf"

    def install(self, runtime) -> ModuleResult:
        return self.activate(runtime)

    def uninstall(self, runtime) -> ModuleResult:
        return self.deactivate(runtime)

    def activate(self, runtime) -> ModuleResult:
        changed = runtime.system.write_text(self.config_path, render_bbr_sysctl())
        runtime.system.run(["sysctl", "--system"], check=True)
        status = self.status(runtime)
        status.operation = Operation.ACTIVATE
        status.changed = changed
        status.message = "BBR sysctl baseline applied."
        return status

    def deactivate(self, runtime) -> ModuleResult:
        changed = runtime.system.remove_file(self.config_path)
        runtime.system.run(["sysctl", "--system"], check=True)
        return ModuleResult(
            code=self.code,
            name=self.name,
            operation=Operation.DEACTIVATE,
            success=True,
            changed=changed,
            message="BBR sysctl baseline removed.",
        )

    def status(self, runtime) -> ModuleResult:
        control = runtime.system.run(["sysctl", "-n", "net.ipv4.tcp_congestion_control"]).stdout.strip()
        available = runtime.system.run(["sysctl", "-n", "net.ipv4.tcp_available_congestion_control"]).stdout.strip()
        qdisc = runtime.system.run(["sysctl", "-n", "net.core.default_qdisc"]).stdout.strip()
        needs_reboot = "bbr" not in available or control != "bbr" or qdisc != "fq"
        return ModuleResult(
            code=self.code,
            name=self.name,
            operation=Operation.STATUS,
            success=True,
            needs_reboot=needs_reboot,
            message="BBR status inspected.",
            details={
                "current_congestion_control": control or "unknown",
                "available_congestion_controls": available or "unknown",
                "default_qdisc": qdisc or "unknown",
                "needs_reboot": "yes" if needs_reboot else "no",
            },
        )

    def info(self, runtime) -> ModuleResult:
        return ModuleResult(
            code=self.code,
            name=self.name,
            operation=Operation.INFO,
            success=True,
            message="BBR manages fq + tcp_congestion_control=bbr via sysctl drop-in.",
            details={"config_path": self.config_path},
        )

