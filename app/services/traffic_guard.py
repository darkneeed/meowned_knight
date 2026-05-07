from __future__ import annotations

from app.core.contracts import ModuleResult, Operation
from app.core.renderers import (
    render_traffic_guard_sysctl,
    render_vpn_camouflage_nginx,
    render_vpn_hardening_notes,
)
from app.services.base import BaseService


class TrafficGuardService(BaseService):
    code = 7
    name = "TrafficGuard"
    config_path = "/etc/sysctl.d/99-hostctl-trafficguard.conf"
    nginx_example_path = "/etc/hostctl/examples/nginx-vpn-camouflage.conf"
    notes_path = "/etc/hostctl/examples/traffic-guard-vpn-notes.txt"

    def install(self, runtime) -> ModuleResult:
        return self.activate(runtime)

    def uninstall(self, runtime) -> ModuleResult:
        return self.deactivate(runtime)

    def activate(self, runtime) -> ModuleResult:
        changed = runtime.system.write_text(self.config_path, render_traffic_guard_sysctl())
        changed |= runtime.system.write_text(self.nginx_example_path, render_vpn_camouflage_nginx())
        changed |= runtime.system.write_text(self.notes_path, render_vpn_hardening_notes())
        runtime.system.run(["sysctl", "--system"], check=True)
        return ModuleResult(
            code=self.code,
            name=self.name,
            operation=Operation.ACTIVATE,
            success=True,
            changed=changed,
            message="Host networking hardening baseline applied with VPN-facing example response policy.",
        )

    def deactivate(self, runtime) -> ModuleResult:
        changed = runtime.system.remove_file(self.config_path)
        changed |= runtime.system.remove_file(self.nginx_example_path)
        changed |= runtime.system.remove_file(self.notes_path)
        runtime.system.run(["sysctl", "--system"], check=True)
        return ModuleResult(
            code=self.code,
            name=self.name,
            operation=Operation.DEACTIVATE,
            success=True,
            changed=changed,
            message="Host networking hardening baseline and VPN-facing examples removed.",
        )

    def status(self, runtime) -> ModuleResult:
        syncookies = runtime.system.run(["sysctl", "-n", "net.ipv4.tcp_syncookies"]).stdout.strip()
        rp_filter = runtime.system.run(["sysctl", "-n", "net.ipv4.conf.all.rp_filter"]).stdout.strip()
        redirects = runtime.system.run(["sysctl", "-n", "net.ipv4.conf.all.accept_redirects"]).stdout.strip()
        return ModuleResult(
            code=self.code,
            name=self.name,
            operation=Operation.STATUS,
            success=True,
            message="TrafficGuard host hardening status inspected.",
            details={
                "syncookies": syncookies or "unknown",
                "rp_filter": rp_filter or "unknown",
                "accept_redirects": redirects or "unknown",
                "config_present": "yes" if runtime.system.file_exists(self.config_path) else "no",
                "nginx_package": "yes" if self.package_installed(runtime, "nginx") else "no",
                "ipset_package": "yes" if self.package_installed(runtime, "ipset") else "no",
                "nginx_example": "present" if runtime.system.file_exists(self.nginx_example_path) else "absent",
                "vpn_notes": "present" if runtime.system.file_exists(self.notes_path) else "absent",
            },
        )

    def info(self, runtime) -> ModuleResult:
        return ModuleResult(
            code=self.code,
            name=self.name,
            operation=Operation.INFO,
            success=True,
            message="TrafficGuard is VPN-oriented: sysctl hardening stays active, while anti-scan behavior is shipped as reviewed examples instead of being forced into live web configs.",
            details={
                "config_path": self.config_path,
                "policy": "silent-drop-or-camouflage",
                "direct_ip_tls": "drop-or-reject-wrong-sni",
                "user_agent_filter": "empty,curl,python-requests,Go-http-client",
                "rkn_strategy": "best-effort-ipset-bgp-feeds",
                "nginx_example_path": self.nginx_example_path,
                "notes_path": self.notes_path,
            },
        )
